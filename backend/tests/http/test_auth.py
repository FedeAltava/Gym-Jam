from unittest.mock import AsyncMock, patch

import pytest

from backend.src.infrastructure.rate_limiter import login_limiter, refresh_limiter, register_limiter

BASE = "/auth"

# Default password satisfies min_length=8, uppercase, and digit requirements.
_DEFAULT_PASSWORD = "Password1"


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiter state before each test to avoid cross-test interference."""
    login_limiter.reset()
    register_limiter.reset()
    refresh_limiter.reset()
    yield
    login_limiter.reset()
    register_limiter.reset()
    refresh_limiter.reset()


# Helpers
async def register(client, email="test@example.com", password=_DEFAULT_PASSWORD):
    return await client.post(f"{BASE}/register", json={"email": email, "password": password})


async def login(client, email="test@example.com", password=_DEFAULT_PASSWORD):
    return await client.post(f"{BASE}/login", json={"email": email, "password": password})


# 1. Register happy path
async def test_register_returns_201(auth_client):
    r = await register(auth_client, "user1@example.com")
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "user1@example.com"
    assert "id" in data


# 2. Register — duplicate email
async def test_register_duplicate_email_returns_409(auth_client):
    await register(auth_client, "dup@example.com")
    r = await register(auth_client, "dup@example.com")
    assert r.status_code == 409


# 3. Register — invalid email
async def test_register_invalid_email_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "not-an-email", "password": "Password1"})
    assert r.status_code == 422


# 4. Register — empty password
async def test_register_empty_password_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "a@example.com", "password": ""})
    assert r.status_code == 422


# 5. Register — missing password
async def test_register_missing_password_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "b@example.com"})
    assert r.status_code == 422


# 6. Login — happy path returns access and refresh tokens
async def test_login_returns_access_token(auth_client):
    await register(auth_client, "login@example.com")
    r = await login(auth_client, "login@example.com")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" not in data  # refresh token is in httpOnly cookie, not body
    assert r.cookies.get("refresh_token"), "Login must set refresh_token httpOnly cookie"
    assert data["token_type"] == "bearer"


# 7. Login — wrong email
async def test_login_wrong_email_returns_401(auth_client):
    r = await login(auth_client, "nobody@example.com")
    assert r.status_code == 401


# 8. Login — wrong password
async def test_login_wrong_password_returns_401(auth_client):
    await register(auth_client, "wrongpw@example.com", "Correct-Password1")
    r = await auth_client.post(f"{BASE}/login", json={"email": "wrongpw@example.com", "password": "wrong"})
    assert r.status_code == 401


# 9. /me — valid token
async def test_me_with_valid_token_returns_user(auth_client):
    await register(auth_client, "me@example.com")
    token_r = await login(auth_client, "me@example.com")
    token = token_r.json()["access_token"]
    r = await auth_client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"


# 10. /me — no token
async def test_me_without_token_returns_401(auth_client):
    r = await auth_client.get(f"{BASE}/me")
    assert r.status_code == 401


# 11. /me — invalid token
async def test_me_with_invalid_token_returns_401(auth_client):
    r = await auth_client.get(f"{BASE}/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401


# 12. Protected workout route — no token
async def test_workout_route_without_token_returns_401(auth_client):
    r = await auth_client.get("/workouts/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 401


# 13. Protected workout route — valid token
async def test_workout_route_with_valid_token_works(auth_client):
    await register(auth_client, "workout_auth@example.com")
    token_r = await login(auth_client, "workout_auth@example.com")
    token = token_r.json()["access_token"]
    r = await auth_client.post(
        "/workouts",
        json={"name": "Auth Test Workout", "training_days": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


# 14. Token payload contains sub and exp, no email
async def test_token_payload_has_sub_and_exp(auth_client):
    import jwt as pyjwt
    from backend.src.infrastructure.config import settings
    await register(auth_client, "payload@example.com")
    token_r = await login(auth_client, "payload@example.com")
    token = token_r.json()["access_token"]
    payload = pyjwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert "sub" in payload
    assert "exp" in payload
    assert "email" not in payload


# 15. Password stored hashed
async def test_password_stored_hashed(auth_client, session):
    import sqlalchemy
    await register(auth_client, "hash@example.com", "MyPlainPassword1")
    result = await session.execute(
        sqlalchemy.text("SELECT hashed_password FROM users WHERE email = 'hash@example.com'")
    )
    row = result.fetchone()
    assert row is not None
    assert row[0].startswith("$2b$")
    assert row[0] != "myplainpassword"


# 16. Register — password too short returns 422
async def test_register_short_password_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "short@example.com", "password": "abc"})
    assert r.status_code == 422


# 17. Register — password exactly at min length (8 chars) with complexity is accepted
async def test_register_password_min_length_accepted(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "minpw@example.com", "password": "Abcde12!"})
    assert r.status_code == 201


# 18. Register — password at max length (72 chars) is accepted
async def test_register_password_max_length_accepted(auth_client):
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "maxpw@example.com", "password": "A1" + "a" * 70},
    )
    assert r.status_code == 201


# 19. Register — password over max length (73 chars) returns 422
async def test_register_password_over_max_length_returns_422(auth_client):
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "toolong@example.com", "password": "a" * 73},
    )
    assert r.status_code == 422


# 19b. Register — multibyte password over 72 BYTES returns 422
# bcrypt truncates at 72 bytes, not 72 characters: 40 x 'ñ' is 40 chars
# but 80 UTF-8 bytes, so it must be rejected.
async def test_register_multibyte_password_over_72_bytes_returns_422(auth_client):
    password = "ñ" * 40  # 40 chars, 80 bytes in UTF-8
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "multibyte@example.com", "password": password},
    )
    assert r.status_code == 422


# 20. Login rate limit — 5 attempts trigger 429
async def test_login_rate_limit_returns_429(auth_client):
    # Exhaust the 5-attempt limit
    for _ in range(5):
        await auth_client.post(f"{BASE}/login", json={"email": "nobody@example.com", "password": "badpass123"})
    r = await auth_client.post(f"{BASE}/login", json={"email": "nobody@example.com", "password": "badpass123"})
    assert r.status_code == 429


# 21. Register rate limit — 10 attempts trigger 429
async def test_register_rate_limit_returns_429(auth_client):
    # Exhaust the 10-attempt limit
    for i in range(10):
        await auth_client.post(
            f"{BASE}/register",
            json={"email": f"ratelimit{i}@example.com", "password": "Password1"},
        )
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "ratelimit_over@example.com", "password": "Password1"},
    )
    assert r.status_code == 429


# 22. Rate limit — client-supplied X-Forwarded-For is IGNORED (spoof bypass closed).
# Rotating XFF values must NOT reset the limit: all requests share the same
# X-Real-IP key, so the 6th attempt is still rejected.
async def test_login_rate_limit_ignores_spoofed_x_forwarded_for(auth_client):
    for i in range(5):
        await auth_client.post(
            f"{BASE}/login",
            json={"email": "nobody@example.com", "password": "badpass123"},
            headers={"X-Real-IP": "203.0.113.10", "X-Forwarded-For": f"10.0.0.{i}"},
        )
    r = await auth_client.post(
        f"{BASE}/login",
        json={"email": "nobody@example.com", "password": "badpass123"},
        headers={"X-Real-IP": "203.0.113.10", "X-Forwarded-For": "10.0.0.99"},
    )
    assert r.status_code == 429


# 23. Rate limit — X-Real-IP (set by nginx, trusted single hop) is honored as the key:
# a different X-Real-IP gets its own bucket and is not blocked.
async def test_login_rate_limit_keys_on_x_real_ip(auth_client):
    for _ in range(5):
        await auth_client.post(
            f"{BASE}/login",
            json={"email": "nobody@example.com", "password": "badpass123"},
            headers={"X-Real-IP": "203.0.113.20"},
        )
    r = await auth_client.post(
        f"{BASE}/login",
        json={"email": "nobody@example.com", "password": "badpass123"},
        headers={"X-Real-IP": "203.0.113.21"},
    )
    assert r.status_code == 401  # not rate-limited — different trusted client IP


# 24. POST /auth/forgot-password — known email → 204
async def test_forgot_password_with_valid_email_returns_204(auth_client):
    await register(auth_client, "forgot@example.com")
    with patch(
        "backend.src.presentation.routers.auth.send_reset_email",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = None
        r = await auth_client.post(f"{BASE}/forgot-password", json={"email": "forgot@example.com"})
    assert r.status_code == 204


# 25. POST /auth/forgot-password — unknown email → 204 (same response — no enumeration)
async def test_forgot_password_with_unknown_email_returns_204(auth_client):
    with patch(
        "backend.src.presentation.routers.auth.send_reset_email",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = None
        r = await auth_client.post(f"{BASE}/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 204


# 26. POST /auth/reset-password — invalid token → 400
async def test_reset_password_with_invalid_token_returns_400(auth_client):
    r = await auth_client.post(
        f"{BASE}/reset-password",
        json={"token": "totally-fake-token", "new_password": "NewPassword1"},
    )
    assert r.status_code == 400


# 27. PATCH /auth/password — no auth header → 401
async def test_change_password_without_auth_returns_401(auth_client):
    r = await auth_client.patch(
        f"{BASE}/password",
        json={"current_password": "Password1", "new_password": "NewPassword1"},
    )
    assert r.status_code == 401


# 28. PATCH /auth/password — authenticated but wrong current password → 400
async def test_change_password_wrong_current_password_returns_400(auth_client):
    await register(auth_client, "changepw@example.com")
    token_r = await login(auth_client, "changepw@example.com")
    token = token_r.json()["access_token"]
    r = await auth_client.patch(
        f"{BASE}/password",
        json={"current_password": "wrong-password", "new_password": "NewPassword1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


# 29. Register — password with no uppercase returns 422
async def test_register_no_uppercase_returns_422(auth_client):
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "nouppercase@example.com", "password": "alllowercase1"},
    )
    assert r.status_code == 422


# 30. Register — password with no digit returns 422
async def test_register_no_digit_returns_422(auth_client):
    r = await auth_client.post(
        f"{BASE}/register",
        json={"email": "nodigit@example.com", "password": "NoDigitHere"},
    )
    assert r.status_code == 422


# 31. PATCH /auth/password — wrong current password returns generic error message
async def test_change_password_wrong_current_returns_generic_message(auth_client):
    await register(auth_client, "changepw_msg@example.com")
    token_r = await login(auth_client, "changepw_msg@example.com")
    token = token_r.json()["access_token"]
    r = await auth_client.patch(
        f"{BASE}/password",
        json={"current_password": "WrongPassword1", "new_password": "NewPassword1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert "wrong" not in detail.lower()
    assert "incorrect" not in detail.lower()


# 32. POST /auth/login — login sets httpOnly refresh_token cookie with correct attributes
async def test_login_sets_httponly_cookie(auth_client):
    await register(auth_client, "cookietest@example.com")
    r = await login(auth_client, "cookietest@example.com")
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/auth" in set_cookie


# 33. POST /auth/refresh — invalid cookie returns 401 and clears the cookie
async def test_refresh_clears_cookie_on_invalid_token(auth_client):
    auth_client.cookies.set("refresh_token", "totally-invalid-token", path="/auth")
    r = await auth_client.post(f"{BASE}/refresh")
    assert r.status_code == 401
    set_cookie = r.headers.get("set-cookie", "")
    # The cookie must be cleared: either Max-Age=0 or an empty value
    assert "refresh_token" in set_cookie
    assert "Max-Age=0" in set_cookie or 'refresh_token=""' in set_cookie or "refresh_token=;" in set_cookie


# 34. POST /auth/logout — clears the refresh_token cookie
async def test_logout_clears_cookie(auth_client):
    await register(auth_client, "logoutcookie@example.com")
    login_r = await login(auth_client, "logoutcookie@example.com")
    assert login_r.status_code == 200
    token = login_r.json()["access_token"]
    r = await auth_client.post(
        f"{BASE}/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204
    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token" in set_cookie
    assert "Max-Age=0" in set_cookie or 'refresh_token=""' in set_cookie or "refresh_token=;" in set_cookie
