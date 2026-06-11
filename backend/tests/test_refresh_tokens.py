from datetime import datetime, timedelta, timezone

from backend.models import PasswordResetToken, RefreshToken, User
from backend.routers.auth import hash_token


def _signup(unauthed_client, email="refresh@example.com"):
    response = unauthed_client.post("/auth/signup", json={
        "email": email,
        "password": "securepass",
        "name": "Refresh",
    })
    assert response.status_code == 201
    return response


def _active_tokens(db, user_id):
    return db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    ).all()


# ── issuance ─────────────────────────────────────────────────────────────────


def test_signup_issues_refresh_cookie(db, unauthed_client):
    _signup(unauthed_client)
    assert unauthed_client.cookies.get("refresh_token") is not None
    user = db.query(User).filter_by(email="refresh@example.com").one()
    assert len(_active_tokens(db, user.id)) == 1


def test_login_issues_refresh_cookie(db, unauthed_client):
    _signup(unauthed_client)
    unauthed_client.post("/auth/logout")
    response = unauthed_client.post("/auth/login", json={
        "email": "refresh@example.com",
        "password": "securepass",
    })
    assert response.status_code == 200
    assert unauthed_client.cookies.get("refresh_token") is not None


def test_refresh_token_stored_hashed(db, unauthed_client):
    _signup(unauthed_client)
    raw = unauthed_client.cookies.get("refresh_token")
    user = db.query(User).filter_by(email="refresh@example.com").one()
    row = _active_tokens(db, user.id)[0]
    assert row.token_hash != raw
    assert row.token_hash == hash_token(raw)


# ── rotation ─────────────────────────────────────────────────────────────────


def test_refresh_rotates_token(db, unauthed_client):
    _signup(unauthed_client)
    old_token = unauthed_client.cookies.get("refresh_token")

    response = unauthed_client.post("/auth/refresh")
    assert response.status_code == 200

    new_token = unauthed_client.cookies.get("refresh_token")
    assert new_token != old_token
    old_row = db.query(RefreshToken).filter_by(token_hash=hash_token(old_token)).one()
    assert old_row.revoked_at is not None
    user = db.query(User).filter_by(email="refresh@example.com").one()
    assert len(_active_tokens(db, user.id)) == 1


def test_refresh_issues_working_access_token(db, unauthed_client):
    _signup(unauthed_client)
    unauthed_client.cookies.delete("access_token")
    assert unauthed_client.get("/auth/me").status_code == 401

    assert unauthed_client.post("/auth/refresh").status_code == 200
    assert unauthed_client.get("/auth/me").status_code == 200


# ── rejection paths ──────────────────────────────────────────────────────────


def test_refresh_without_cookie_401(unauthed_client):
    assert unauthed_client.post("/auth/refresh").status_code == 401


def test_refresh_with_unknown_token_401(unauthed_client):
    unauthed_client.cookies.set("refresh_token", "not-a-real-token")
    assert unauthed_client.post("/auth/refresh").status_code == 401


def test_refresh_with_expired_token_401(db, unauthed_client):
    _signup(unauthed_client)
    user = db.query(User).filter_by(email="refresh@example.com").one()
    raw = "expired-raw-token"
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    ))
    db.commit()
    unauthed_client.cookies.set("refresh_token", raw)
    assert unauthed_client.post("/auth/refresh").status_code == 401


def test_reused_token_revokes_all_sessions(db, unauthed_client):
    """Rotation means each refresh token is presented at most once — a second
    presentation is theft, and every session for the user gets burned."""
    _signup(unauthed_client)
    stolen = unauthed_client.cookies.get("refresh_token")

    assert unauthed_client.post("/auth/refresh").status_code == 200

    unauthed_client.cookies.set("refresh_token", stolen)
    assert unauthed_client.post("/auth/refresh").status_code == 401

    user = db.query(User).filter_by(email="refresh@example.com").one()
    assert _active_tokens(db, user.id) == []


# ── revocation on logout / password reset ────────────────────────────────────


def test_logout_revokes_refresh_token(db, unauthed_client):
    _signup(unauthed_client)
    raw = unauthed_client.cookies.get("refresh_token")

    assert unauthed_client.post("/auth/logout").status_code == 200

    row = db.query(RefreshToken).filter_by(token_hash=hash_token(raw)).one()
    assert row.revoked_at is not None
    # even if the cookie were stolen before logout, it is now dead
    unauthed_client.cookies.set("refresh_token", raw)
    assert unauthed_client.post("/auth/refresh").status_code == 401


def test_reset_password_revokes_all_refresh_tokens(db, unauthed_client):
    _signup(unauthed_client)
    user = db.query(User).filter_by(email="refresh@example.com").one()
    reset_raw = "plain-test-reset-token"
    db.add(PasswordResetToken(
        user_id=user.id,
        token=hash_token(reset_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ))
    db.commit()

    response = unauthed_client.post("/auth/reset-password", json={
        "token": reset_raw,
        "new_password": "brandnewpass",
    })
    assert response.status_code == 200
    assert _active_tokens(db, user.id) == []
