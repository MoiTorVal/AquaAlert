import pytest

from backend.rate_limit import limiter


@pytest.fixture
def rate_limited():
    """Turn the limiter on for this test only (autouse fixture disables it)."""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False
    limiter.reset()


def test_login_rate_limited_after_5(unauthed_client, rate_limited):
    payload = {"email": "nobody@example.com", "password": "wrongpass"}

    # AUTH_WRITE_LIMIT is 5/minute; the 6th request from the same client
    # must be throttled rather than hitting the auth logic again.
    statuses = [
        unauthed_client.post("/auth/login", json=payload).status_code
        for _ in range(6)
    ]
    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429


def test_limit_resets_between_tests(unauthed_client):
    # autouse fixture disabled the limiter again, so a burst is fine.
    statuses = [
        unauthed_client.post(
            "/auth/login", json={"email": "x@example.com", "password": "y"}
        ).status_code
        for _ in range(8)
    ]
    assert all(s == 401 for s in statuses)
