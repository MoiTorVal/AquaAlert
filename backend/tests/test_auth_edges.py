from datetime import datetime, timedelta, timezone

import jwt

from backend.auth import create_access_token, SECRET_KEY, ALGORITHM
from backend.models import PasswordResetToken
from backend.routers.auth import hash_token


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
