from datetime import timedelta

import jwt

from backend.auth import create_access_token, SECRET_KEY, ALGORITHM


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
