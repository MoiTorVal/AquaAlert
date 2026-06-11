import asyncio
import base64
import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import SecretStr

from backend import crud, models
from backend.config import settings
from backend.enums import AlertFeedback, IrrigationSource, Locale, StressSeverity
from backend.schemas import FarmCreate, IrrigationEventCreate
from backend.services import sms_service
from backend.services.sms_service import (
    SmsError,
    SmsNotConfiguredError,
    send_sms,
    stress_alert_body,
    validate_signature,
)

TWILIO_SID = "ACtest00000000000000000000000000"
AUTH_TOKEN = "twilio-auth-token"
FROM_NUMBER = "+15550006666"
WEBHOOK_URL = "https://api.example.com/sms/webhook"
FARMER_PHONE = "+15551112222"


@pytest.fixture
def twilio_configured(monkeypatch):
    monkeypatch.setattr(settings, "twilio_account_sid", TWILIO_SID)
    monkeypatch.setattr(settings, "twilio_auth_token", SecretStr(AUTH_TOKEN))
    monkeypatch.setattr(settings, "twilio_from_number", FROM_NUMBER)
    monkeypatch.setattr(settings, "sms_webhook_url", WEBHOOK_URL)
    monkeypatch.setattr(sms_service, "RETRY_BASE_DELAY_S", 0)


@pytest.fixture
def twilio_unconfigured(monkeypatch):
    """Explicit, so these tests survive real Twilio keys landing in .env."""
    monkeypatch.setattr(settings, "twilio_account_sid", None)
    monkeypatch.setattr(settings, "twilio_auth_token", None)
    monkeypatch.setattr(settings, "twilio_from_number", None)
    monkeypatch.setattr(settings, "sms_webhook_url", None)


@pytest.fixture
def sms_user(db, user):
    user.phone_number = FARMER_PHONE
    user.sms_alerts_enabled = True
    db.commit()
    return user


# ── send_sms ─────────────────────────────────────────────────────────────────


def _send(transport):
    return asyncio.run(send_sms(FARMER_PHONE, "hello", transport=transport))


def test_send_sms_posts_message_and_returns_sid(twilio_configured):
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers["Authorization"]
        seen["form"] = {k: v[0] for k, v in parse_qs(request.content.decode()).items()}
        return httpx.Response(201, json={"sid": "SM123"})

    assert _send(httpx.MockTransport(handler)) == "SM123"
    assert seen["path"] == f"/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    expected_auth = base64.b64encode(f"{TWILIO_SID}:{AUTH_TOKEN}".encode()).decode()
    assert seen["auth"] == f"Basic {expected_auth}"
    assert seen["form"] == {"To": FARMER_PHONE, "From": FROM_NUMBER, "Body": "hello"}


def test_send_sms_unconfigured_raises(twilio_unconfigured):
    with pytest.raises(SmsNotConfiguredError):
        _send(httpx.MockTransport(lambda req: httpx.Response(201, json={"sid": "SM1"})))


def test_send_sms_4xx_raises_without_retry(twilio_configured):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(400, text="invalid To number")

    with pytest.raises(SmsError, match="invalid To number"):
        _send(httpx.MockTransport(handler))
    assert len(calls) == 1


def test_send_sms_5xx_retries_then_raises(twilio_configured):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503, text="overloaded")

    with pytest.raises(SmsError):
        _send(httpx.MockTransport(handler))
    assert len(calls) == sms_service.MAX_ATTEMPTS


def test_send_sms_transport_error_retries_then_raises(twilio_configured):
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ConnectTimeout("timed out")

    with pytest.raises(SmsError):
        _send(httpx.MockTransport(handler))
    assert len(calls) == sms_service.MAX_ATTEMPTS


def test_send_sms_5xx_then_success_recovers(twilio_configured):
    responses = iter([
        httpx.Response(500, text="hiccup"),
        httpx.Response(201, json={"sid": "SM456"}),
    ])
    assert _send(httpx.MockTransport(lambda req: next(responses))) == "SM456"


# ── signature validation ─────────────────────────────────────────────────────

# Worked example from https://www.twilio.com/docs/usage/security
DOCS_URL = "https://example.com/myapp.php?foo=1&bar=2"
DOCS_PARAMS = {
    "CallSid": "CA1234567890ABCDE",
    "Caller": "+14158675310",
    "Digits": "1234",
    "From": "+14158675310",
    "To": "+18005551212",
}
DOCS_SIGNATURE = "L/OH5YylLD5NRKLltdqwSvS0BnU="


def test_validate_signature_twilio_docs_vector(monkeypatch):
    monkeypatch.setattr(settings, "twilio_auth_token", SecretStr("12345"))
    assert validate_signature(DOCS_URL, DOCS_PARAMS, DOCS_SIGNATURE) is True


def test_validate_signature_rejects_tampered_params(monkeypatch):
    monkeypatch.setattr(settings, "twilio_auth_token", SecretStr("12345"))
    assert validate_signature(DOCS_URL, {**DOCS_PARAMS, "Digits": "9999"}, DOCS_SIGNATURE) is False


def test_validate_signature_without_token_rejects(twilio_unconfigured):
    assert validate_signature(DOCS_URL, DOCS_PARAMS, DOCS_SIGNATURE) is False


# ── message copy ─────────────────────────────────────────────────────────────


def test_stress_alert_body_en_red_with_days():
    body = stress_alert_body(Locale.EN, "North Field", StressSeverity.RED, date(2026, 6, 9), 3)
    assert "North Field" in body
    assert "RED" in body
    assert "2026-06-09" in body
    assert "~3 days" in body
    assert "Reply 1" in body


def test_stress_alert_body_es_yellow():
    body = stress_alert_body(Locale.ES, "Campo Sur", StressSeverity.YELLOW, date(2026, 6, 9), 5)
    assert "AMARILLO" in body
    assert "~5 días" in body
    assert "Responda" in body


def test_stress_alert_body_omits_days_when_zero_or_none():
    at_stress = stress_alert_body(Locale.EN, "F", StressSeverity.RED, date(2026, 6, 9), 0)
    unknown = stress_alert_body(Locale.EN, "F", StressSeverity.RED, date(2026, 6, 9), None)
    assert "days to crop stress" not in at_stress
    assert "days to crop stress" not in unknown


# ── webhook ──────────────────────────────────────────────────────────────────


def _sign(params: dict) -> str:
    payload = WEBHOOK_URL + "".join(k + v for k, v in sorted(params.items()))
    digest = hmac.new(AUTH_TOKEN.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _post_sms(client, body, from_number=FARMER_PHONE):
    params = {"From": from_number, "Body": body, "MessageSid": "SMinbound"}
    return client.post("/sms/webhook", data=params, headers={"X-Twilio-Signature": _sign(params)})


def test_webhook_unconfigured_returns_503(unauthed_client, twilio_unconfigured):
    assert _post_sms(unauthed_client, "1").status_code == 503


def test_webhook_invalid_signature_returns_403(unauthed_client, twilio_configured):
    response = unauthed_client.post(
        "/sms/webhook",
        data={"From": FARMER_PHONE, "Body": "1"},
        headers={"X-Twilio-Signature": "bogus"},
    )
    assert response.status_code == 403


def test_webhook_unknown_sender_gets_empty_twiml(unauthed_client, twilio_configured):
    response = _post_sms(unauthed_client, "1", from_number="+19998887777")
    assert response.status_code == 200
    assert "<Message>" not in response.text


def test_webhook_logs_explicit_gallons(unauthed_client, db, twilio_configured, sms_user, farm):
    response = _post_sms(unauthed_client, "1 5000")
    assert response.status_code == 200
    assert "Logged 5000 gal" in response.text
    (event,) = crud.get_irrigation_events_by_farm(db, farm_id=farm.id)
    assert event.gallons_applied == Decimal("5000.00")
    assert event.source == IrrigationSource.USER_LOG
    assert event.event_date == date.today()


def test_webhook_bare_one_without_history_asks_for_gallons(unauthed_client, db, twilio_configured, sms_user, farm):
    response = _post_sms(unauthed_client, "1")
    assert "'1' plus gallons" in response.text
    assert crud.count_irrigation_events_by_farm(db, farm_id=farm.id) == 0


def test_webhook_bare_one_inherits_usual_gallons_as_estimated(unauthed_client, db, twilio_configured, sms_user, farm):
    crud.create_irrigation_event(db, farm.id, IrrigationEventCreate(
        event_date=date.today() - timedelta(days=3), gallons_applied=Decimal("2500"),
    ))
    response = _post_sms(unauthed_client, "1")
    assert "~2500 gal" in response.text
    events = crud.get_irrigation_events_by_farm(db, farm_id=farm.id)
    today_event = next(e for e in events if e.event_date == date.today())
    assert today_event.gallons_applied == Decimal("2500.00")
    assert today_event.source == IrrigationSource.ESTIMATED


def test_webhook_tolerates_extra_whitespace(unauthed_client, db, twilio_configured, sms_user, farm):
    _post_sms(unauthed_client, "  1   2500 ")
    (event,) = crud.get_irrigation_events_by_farm(db, farm_id=farm.id)
    assert event.gallons_applied == Decimal("2500.00")


def test_webhook_rejects_zero_gallons(unauthed_client, db, twilio_configured, sms_user, farm):
    response = _post_sms(unauthed_client, "1 0")
    assert "reply 1 after you irrigate" in response.text.lower()  # help message
    assert crud.count_irrigation_events_by_farm(db, farm_id=farm.id) == 0


def test_webhook_multi_farm_without_alert_asks_to_use_app(unauthed_client, db, twilio_configured, sms_user, farm):
    crud.create_farm(db, FarmCreate(name="Second Farm"), user_id=sms_user.id)
    response = _post_sms(unauthed_client, "1 5000")
    assert "multiple farms" in response.text
    assert crud.count_irrigation_events_by_farm(db, farm_id=farm.id) == 0


def test_webhook_multi_farm_logs_to_most_recently_alerted(unauthed_client, db, twilio_configured, sms_user, farm):
    second = crud.create_farm(db, FarmCreate(name="Second Farm"), user_id=sms_user.id)
    crud.create_alert(db, farm_id=second.id, severity=StressSeverity.RED,
                      as_of_date=date.today(), days_to_stress=2, provider_message_sid="SM1")
    _post_sms(unauthed_client, "1 5000")
    assert crud.count_irrigation_events_by_farm(db, farm_id=second.id) == 1
    assert crud.count_irrigation_events_by_farm(db, farm_id=farm.id) == 0


def test_webhook_yes_records_feedback(unauthed_client, db, twilio_configured, sms_user, farm):
    alert = crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.RED,
                              as_of_date=date.today(), days_to_stress=2, provider_message_sid="SM1")
    response = _post_sms(unauthed_client, "Y")
    assert "Thanks" in response.text
    db.refresh(alert)
    assert alert.feedback == AlertFeedback.YES
    assert alert.feedback_at is not None


def test_webhook_lowercase_no_records_feedback(unauthed_client, db, twilio_configured, sms_user, farm):
    alert = crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.YELLOW,
                              as_of_date=date.today(), days_to_stress=4, provider_message_sid="SM1")
    _post_sms(unauthed_client, "n")
    db.refresh(alert)
    assert alert.feedback == AlertFeedback.NO


def test_webhook_spanish_user_s_means_yes(unauthed_client, db, twilio_configured, sms_user, farm):
    sms_user.locale = Locale.ES
    db.commit()
    alert = crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.RED,
                              as_of_date=date.today(), days_to_stress=2, provider_message_sid="SM1")
    response = _post_sms(unauthed_client, "S")
    assert "Gracias" in response.text
    db.refresh(alert)
    assert alert.feedback == AlertFeedback.YES


def test_webhook_feedback_without_recent_alert(unauthed_client, db, twilio_configured, sms_user, farm):
    response = _post_sms(unauthed_client, "Y")
    assert "No recent alert" in response.text


def test_webhook_feedback_ignores_stale_alert(unauthed_client, db, twilio_configured, sms_user, farm):
    alert = crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.RED,
                              as_of_date=date.today() - timedelta(days=8),
                              days_to_stress=2, provider_message_sid="SM1")
    alert.sent_at = datetime.now(timezone.utc) - timedelta(days=8)
    db.commit()
    response = _post_sms(unauthed_client, "Y")
    assert "No recent alert" in response.text
    db.refresh(alert)
    assert alert.feedback is None


def test_webhook_unrecognized_reply_gets_help(unauthed_client, twilio_configured, sms_user):
    response = _post_sms(unauthed_client, "what is this")
    assert "reply 1 after you irrigate" in response.text.lower()


def test_webhook_escapes_twiml_content(unauthed_client, db, twilio_configured, sms_user):
    crud.create_farm(db, FarmCreate(name="Bob & Sons <Farm>"), user_id=sms_user.id)
    response = _post_sms(unauthed_client, "1 5000")
    assert "Bob &amp; Sons &lt;Farm&gt;" in response.text


# ── alert history endpoint ───────────────────────────────────────────────────


def test_list_alerts_newest_first_without_internal_fields(client, db, farm):
    old = crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.YELLOW,
                            as_of_date=date.today() - timedelta(days=3),
                            days_to_stress=4, provider_message_sid="SM1")
    old.sent_at = datetime.now(timezone.utc) - timedelta(days=3)
    db.commit()
    crud.create_alert(db, farm_id=farm.id, severity=StressSeverity.RED,
                      as_of_date=date.today(), days_to_stress=1, provider_message_sid="SM2")

    body = client.get(f"/farms/{farm.id}/alerts").json()
    assert body["total"] == 2
    assert [r["severity"] for r in body["results"]] == ["red", "yellow"]
    assert "provider_message_sid" not in body["results"][0]
    assert body["results"][0]["feedback"] is None


def test_list_alerts_other_users_farm_404(client, db, user):
    other = models.User(email="other@example.com", hashed_password="x", name="Other")
    db.add(other)
    db.commit()
    other_farm = crud.create_farm(db, FarmCreate(name="Not Yours"), user_id=other.id)
    assert client.get(f"/farms/{other_farm.id}/alerts").status_code == 404


# ── profile SMS settings (PATCH /auth/me) ────────────────────────────────────


def test_patch_me_sets_phone(client):
    response = client.patch("/auth/me", json={"phone_number": FARMER_PHONE})
    assert response.status_code == 200
    assert response.json()["phone_number"] == FARMER_PHONE
    assert response.json()["sms_alerts_enabled"] is False


def test_patch_me_rejects_invalid_phone(client):
    assert client.patch("/auth/me", json={"phone_number": "555-123"}).status_code == 422


def test_patch_me_enable_sms_without_phone_400(client):
    response = client.patch("/auth/me", json={"sms_alerts_enabled": True})
    assert response.status_code == 400
    assert "phone number" in response.json()["detail"]


def test_patch_me_phone_and_enable_together(client):
    response = client.patch("/auth/me", json={"phone_number": FARMER_PHONE, "sms_alerts_enabled": True})
    assert response.status_code == 200
    assert response.json()["sms_alerts_enabled"] is True


def test_patch_me_clearing_phone_while_enabled_400(client, db, sms_user):
    response = client.patch("/auth/me", json={"phone_number": None})
    assert response.status_code == 400


def test_patch_me_duplicate_phone_400(client, db):
    other = models.User(email="other@example.com", hashed_password="x",
                        name="Other", phone_number=FARMER_PHONE)
    db.add(other)
    db.commit()
    response = client.patch("/auth/me", json={"phone_number": FARMER_PHONE})
    assert response.status_code == 400
    assert "already in use" in response.json()["detail"]
