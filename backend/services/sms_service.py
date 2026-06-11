"""Twilio SMS: outbound alert delivery + inbound webhook signature validation.

Raw REST API via httpx (matches openet/cimis client style; the Twilio SDK
would be a heavy dependency for two calls). All message copy lives here so
EN/ES stay side by side and in sync.
"""
import asyncio
import base64
import hashlib
import hmac
import logging
from collections.abc import Mapping
from datetime import date

import httpx

from backend.config import settings
from backend.enums import Locale, StressSeverity

logger = logging.getLogger(__name__)

TWILIO_BASE_URL = "https://api.twilio.com"
REQUEST_TIMEOUT_S = 30.0
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0


class SmsError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class SmsNotConfiguredError(SmsError):
    pass


def is_configured() -> bool:
    return (
        settings.twilio_account_sid is not None
        and settings.twilio_auth_token is not None
        and settings.twilio_from_number is not None
    )


async def send_sms(to: str, body: str, transport: httpx.AsyncBaseTransport | None = None) -> str:
    """Send one SMS; returns the Twilio message SID. Raises SmsError."""
    if not is_configured():
        raise SmsNotConfiguredError("Twilio is not configured")
    path = f"/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    auth = (settings.twilio_account_sid, settings.twilio_auth_token.get_secret_value())
    data = {"To": to, "From": settings.twilio_from_number, "Body": body}

    last_error: SmsError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(
                base_url=TWILIO_BASE_URL, timeout=REQUEST_TIMEOUT_S, auth=auth, transport=transport
            ) as client:
                response = await client.post(path, data=data)
        except httpx.RequestError as exc:
            last_error = SmsError(f"Twilio request failed: {exc}")
            logger.warning("Twilio request error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, exc)
        else:
            if response.status_code == 201:
                return response.json()["sid"]
            detail = f"Twilio returned {response.status_code}: {response.text[:200]}"
            if response.status_code >= 500:
                last_error = SmsError(detail, status_code=response.status_code)
                logger.warning("Twilio server error (attempt %d/%d): %s", attempt, MAX_ATTEMPTS, detail)
            else:
                # 4xx (bad number, auth, ...) — retrying cannot help
                raise SmsError(detail, status_code=response.status_code)
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(RETRY_BASE_DELAY_S * 2 ** (attempt - 1))
    raise last_error


def validate_signature(url: str, params: Mapping[str, str], signature: str) -> bool:
    """Twilio webhook auth: base64(HMAC-SHA1(auth_token, url + sorted params)).

    https://www.twilio.com/docs/usage/security#validating-requests
    """
    if settings.twilio_auth_token is None:
        return False
    payload = url + "".join(key + value for key, value in sorted(params.items()))
    digest = hmac.new(
        settings.twilio_auth_token.get_secret_value().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode("ascii"), signature)


# ── message copy (EN/ES) ─────────────────────────────────────────────────────

_SEVERITY_LABELS = {
    StressSeverity.YELLOW: {Locale.EN: "YELLOW", Locale.ES: "AMARILLO"},
    StressSeverity.RED: {Locale.EN: "RED", Locale.ES: "ROJO"},
}

_MESSAGES = {
    Locale.EN: {
        "alert": "AquaAlert: {farm} is at {severity} water stress (as of {as_of}).",
        "alert_days": " ~{days} days to crop stress at the current pace.",
        "alert_actions": " Reply 1 after you irrigate (or '1 5000' = gallons). Reply Y/N: does the crop look stressed?",
        "logged": "Logged {gallons} gal for {farm} on {event_date}. Thanks!",
        "logged_estimated": "Logged ~{gallons} gal (your usual amount) for {farm} on {event_date}. Reply '1 5000' next time to set exact gallons.",
        "need_gallons": "We don't have a usual amount for {farm} yet. Reply with '1' plus gallons, e.g. '1 5000'.",
        "which_farm": "You have multiple farms — please log irrigation in the app so it lands on the right one.",
        "feedback_thanks": "Thanks — noted for {farm}. This helps make alerts more accurate.",
        "no_recent_alert": "No recent alert to attach that to. Reply 1 to log irrigation, or manage your farms in the app.",
        "help": "AquaAlert: reply 1 after you irrigate (or '1 5000' = gallons). After an alert, reply Y or N to tell us if the crop looked stressed.",
    },
    Locale.ES: {
        "alert": "AquaAlert: {farm} está en estrés hídrico {severity} (al {as_of}).",
        "alert_days": " ~{days} días hasta estrés del cultivo al ritmo actual.",
        "alert_actions": " Responda 1 después de regar (o '1 5000' = galones). Responda S/N: ¿se ve estresado el cultivo?",
        "logged": "Registrado: {gallons} gal para {farm} el {event_date}. ¡Gracias!",
        "logged_estimated": "Registrado: ~{gallons} gal (su cantidad habitual) para {farm} el {event_date}. Responda '1 5000' la próxima vez para indicar galones exactos.",
        "need_gallons": "Aún no tenemos una cantidad habitual para {farm}. Responda '1' más los galones, p. ej. '1 5000'.",
        "which_farm": "Tiene varias granjas — registre el riego en la aplicación para que quede en la correcta.",
        "feedback_thanks": "Gracias — anotado para {farm}. Esto ayuda a mejorar las alertas.",
        "no_recent_alert": "No hay alerta reciente para asociar. Responda 1 para registrar riego, o use la aplicación.",
        "help": "AquaAlert: responda 1 después de regar (o '1 5000' = galones). Tras una alerta, responda S o N para indicar si el cultivo se veía estresado.",
    },
}


def message(locale: Locale, key: str, **kwargs) -> str:
    return _MESSAGES[locale][key].format(**kwargs)


def stress_alert_body(
    locale: Locale,
    farm_name: str,
    severity: StressSeverity,
    as_of: date,
    days_to_stress: int | None,
) -> str:
    body = message(
        locale, "alert",
        farm=farm_name, severity=_SEVERITY_LABELS[severity][locale], as_of=as_of.isoformat(),
    )
    if days_to_stress is not None and days_to_stress > 0:
        body += message(locale, "alert_days", days=days_to_stress)
    return body + message(locale, "alert_actions")
