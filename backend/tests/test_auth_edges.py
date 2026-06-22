import logging
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.exc import IntegrityError

from backend import models
from backend.auth import create_access_token, SECRET_KEY, ALGORITHM
from backend.config import settings
from backend.models import PasswordResetToken
from backend.routers.auth import hash_token


def test_signup_password_too_short(unauthed_client):
    response = unauthed_client.post("/auth/signup", json={
        "email": "short@example.com",
        "password": "short",
        "name": "Short Pass",
    })
    assert response.status_code == 422


def test_signup_race_duplicate_email_returns_400(unauthed_client, db, monkeypatch):
    """Two concurrent signups can both pass the existence check; the unique
    constraint fires on commit and must surface as 400, not 500."""
    def conflict():
        raise IntegrityError("INSERT INTO users", {}, Exception("duplicate key"))

    monkeypatch.setattr(db, "commit", conflict)
    response = unauthed_client.post("/auth/signup", json={
        "email": "race@example.com",
        "password": "securepass",
        "name": "Racer",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_signup_invalid_email(unauthed_client):
    response = unauthed_client.post("/auth/signup", json={
        "email": "not-an-email",
        "password": "securepass",
        "name": "Bad Email",
    })
    assert response.status_code == 422


def test_forgot_password_same_response_for_known_and_unknown(unauthed_client, user):
    known = unauthed_client.post("/auth/forgot-password", json={"email": user.email})
    unknown = unauthed_client.post("/auth/forgot-password", json={"email": "ghost@example.com"})
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]


def test_invalid_token_rejected(unauthed_client):
    unauthed_client.cookies.set("access_token", "thisistotallynotavalidtoken")
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401


def test_missing_token_rejected(unauthed_client):
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401


def test_expired_token_rejected(unauthed_client):
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    unauthed_client.cookies.set("access_token", token)
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_token_missing_sub_rejected(unauthed_client):
    token = jwt.encode({"exp": 9999999999}, SECRET_KEY, algorithm=ALGORITHM)
    unauthed_client.cookies.set("access_token", token)
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401


def test_token_non_int_sub_rejected(unauthed_client):
    token = create_access_token({"sub": "notanint"})
    unauthed_client.cookies.set("access_token", token)
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401


def test_token_deleted_user_rejected(unauthed_client):
    token = create_access_token({"sub": "99999"})
    unauthed_client.cookies.set("access_token", token)
    response = unauthed_client.get("/farms/")
    assert response.status_code == 401


# ── iat / password-reset token invalidation ──────────────────────────────────


def _backdated_token(user_id, minutes):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now - timedelta(minutes=minutes), "exp": now + timedelta(hours=2)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def test_create_access_token_sets_iat():
    payload = jwt.decode(create_access_token({"sub": "1"}), SECRET_KEY, algorithms=[ALGORITHM])
    assert abs(payload["iat"] - datetime.now(timezone.utc).timestamp()) < 5


def test_token_issued_before_password_reset_rejected(db, unauthed_client, user):
    old_token = _backdated_token(user.id, minutes=10)
    token = _create_reset_token(db, user, timedelta(hours=1))
    response = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    assert response.status_code == 200

    unauthed_client.cookies.set("access_token", old_token)
    assert unauthed_client.get("/auth/me").status_code == 401


def test_fresh_token_after_password_reset_accepted(db, unauthed_client, user):
    token = _create_reset_token(db, user, timedelta(hours=1))
    unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    # login immediately after the reset — must not trip the iat guard even
    # within the same second (iat is truncated to whole seconds)
    login = unauthed_client.post("/auth/login", json={
        "email": user.email,
        "password": "brandnewpass",
    })
    assert login.status_code == 200
    assert unauthed_client.get("/auth/me").status_code == 200


def test_legacy_token_without_iat_still_accepted(unauthed_client, user):
    """Tokens minted before the iat claim shipped stay valid until expiry."""
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(hours=2)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    unauthed_client.cookies.set("access_token", token)
    assert unauthed_client.get("/auth/me").status_code == 200


# ── reset password ───────────────────────────────────────────────────────────


def _create_reset_token(db, user, expires_delta):
    token = "plain-test-reset-token"
    db.add(PasswordResetToken(
        user_id=user.id,
        token=hash_token(token),
        expires_at=datetime.now(timezone.utc) + expires_delta,
    ))
    db.commit()
    return token


def test_reset_password_valid_token(db, unauthed_client, user):
    token = _create_reset_token(db, user, timedelta(hours=1))
    response = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    assert response.status_code == 200

    login = unauthed_client.post("/auth/login", json={
        "email": user.email,
        "password": "brandnewpass",
    })
    assert login.status_code == 200


def test_reset_password_expired_token(db, unauthed_client, user):
    token = _create_reset_token(db, user, timedelta(hours=-1))
    response = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


def test_reset_password_unknown_token(unauthed_client):
    response = unauthed_client.post("/auth/reset-password", json={
        "token": "never-issued",
        "new_password": "brandnewpass",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


def test_reset_password_too_short_rejected(db, unauthed_client, user):
    token = _create_reset_token(db, user, timedelta(hours=1))
    response = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "short",
    })
    assert response.status_code == 422


def test_forgot_password_logs_link_only_when_enabled(unauthed_client, user, monkeypatch, caplog):
    monkeypatch.setattr(settings, "log_reset_links", False)
    with caplog.at_level(logging.INFO, logger="backend.routers.auth"):
        unauthed_client.post("/auth/forgot-password", json={"email": user.email})
    assert "reset-password?token=" not in caplog.text

    monkeypatch.setattr(settings, "log_reset_links", True)
    with caplog.at_level(logging.INFO, logger="backend.routers.auth"):
        unauthed_client.post("/auth/forgot-password", json={"email": user.email})
    assert f"{settings.frontend_base_url}/reset-password?token=" in caplog.text


def test_reset_password_token_single_use(db, unauthed_client, user):
    token = _create_reset_token(db, user, timedelta(hours=1))
    first = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    assert first.status_code == 200
    second = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "anotherpass1",
    })
    assert second.status_code == 400


def test_reset_password_user_gone_returns_400(db, unauthed_client, user, monkeypatch):
    """Defensive branch: the FK makes an orphaned token impossible today, but
    the route must still 400 (not 500) if the user lookup ever comes back empty."""
    token = _create_reset_token(db, user, timedelta(hours=1))

    class _NoUser:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

    real_query = db.query
    monkeypatch.setattr(
        db, "query",
        lambda model, *a: _NoUser() if model is models.User else real_query(model, *a),
    )
    response = unauthed_client.post("/auth/reset-password", json={
        "token": token,
        "new_password": "brandnewpass",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired token"


# ── logout ───────────────────────────────────────────────────────────────────


def test_logout_clears_auth_cookie(unauthed_client):
    unauthed_client.post("/auth/signup", json={
        "email": "bye@example.com",
        "password": "securepass",
        "name": "Bye",
    })
    assert unauthed_client.get("/auth/me").status_code == 200

    response = unauthed_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"
    set_cookie = response.headers["set-cookie"]
    assert "access_token=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "HttpOnly" in set_cookie
    # the browser-side cookie is gone, so the session is over
    assert unauthed_client.get("/auth/me").status_code == 401


def test_logout_without_session_still_succeeds(unauthed_client):
    response = unauthed_client.post("/auth/logout")
    assert response.status_code == 200


def test_patch_me_updates_locale(client):
    response = client.patch("/auth/me", json={"locale": "es"})
    assert response.status_code == 200
    assert response.json()["locale"] == "es"


def test_patch_me_sets_equity_flags(client):
    response = client.patch("/auth/me", json={
        "is_socially_disadvantaged": True,
        "is_beginning_farmer": False,
    })
    assert response.status_code == 200
    body = response.json()
    assert body["is_socially_disadvantaged"] is True
    assert body["is_beginning_farmer"] is False


def test_patch_me_explicit_null_clears_equity_answer(client):
    client.patch("/auth/me", json={"is_beginning_farmer": True})
    response = client.patch("/auth/me", json={"is_beginning_farmer": None})
    assert response.status_code == 200
    assert response.json()["is_beginning_farmer"] is None


def test_patch_me_omitted_fields_untouched(client):
    client.patch("/auth/me", json={"locale": "es", "is_beginning_farmer": True})
    response = client.patch("/auth/me", json={"locale": "en"})
    body = response.json()
    assert body["locale"] == "en"
    assert body["is_beginning_farmer"] is True


def test_patch_me_rejects_unknown_locale(client):
    response = client.patch("/auth/me", json={"locale": "fr"})
    assert response.status_code == 422


def test_patch_me_unauthenticated(unauthed_client):
    response = unauthed_client.patch("/auth/me", json={"locale": "es"})
    assert response.status_code == 401


def test_auth_write_rejects_untrusted_origin(unauthed_client):
    response = unauthed_client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


def test_patch_me_rejects_untrusted_origin(client):
    response = client.patch(
        "/auth/me",
        json={"locale": "es"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Untrusted request origin"


# ── password length limits ───────────────────────────────────────────────────


def test_signup_rejects_password_over_72_bytes(unauthed_client):
    # bcrypt only hashes the first 72 bytes; we reject instead of truncating
    response = unauthed_client.post("/auth/signup", json={
        "email": "longpw@example.com",
        "password": "x" * 73,
        "name": "Long",
    })
    assert response.status_code == 422


def test_signup_rejects_password_over_72_bytes_multibyte(unauthed_client):
    # 25 chars but 75 bytes in UTF-8 — the byte limit is what bcrypt sees
    response = unauthed_client.post("/auth/signup", json={
        "email": "emoji@example.com",
        "password": "€" * 25,
        "name": "Emoji",
    })
    assert response.status_code == 422


def test_reset_password_rejects_password_over_72_bytes(unauthed_client):
    response = unauthed_client.post("/auth/reset-password", json={
        "token": "irrelevant",
        "new_password": "x" * 73,
    })
    assert response.status_code == 422
