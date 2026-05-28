import pytest

BASE = "/auth"


# Helpers
async def register(client, email="test@example.com", password="password123"):
    return await client.post(f"{BASE}/register", json={"email": email, "password": password})


async def login(client, email="test@example.com", password="password123"):
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
    r = await auth_client.post(f"{BASE}/register", json={"email": "not-an-email", "password": "password123"})
    assert r.status_code == 422


# 4. Register — empty password
async def test_register_empty_password_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "a@example.com", "password": ""})
    assert r.status_code == 422


# 5. Register — missing password
async def test_register_missing_password_returns_422(auth_client):
    r = await auth_client.post(f"{BASE}/register", json={"email": "b@example.com"})
    assert r.status_code == 422


# 6. Login — happy path returns token
async def test_login_returns_access_token(auth_client):
    await register(auth_client, "login@example.com")
    r = await login(auth_client, "login@example.com")
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 7. Login — wrong email
async def test_login_wrong_email_returns_401(auth_client):
    r = await login(auth_client, "nobody@example.com")
    assert r.status_code == 401


# 8. Login — wrong password
async def test_login_wrong_password_returns_401(auth_client):
    await register(auth_client, "wrongpw@example.com", "correct-password")
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
    await register(auth_client, "hash@example.com", "myplainpassword")
    result = await session.execute(
        sqlalchemy.text("SELECT hashed_password FROM users WHERE email = 'hash@example.com'")
    )
    row = result.fetchone()
    assert row is not None
    assert row[0].startswith("$2b$")
    assert row[0] != "myplainpassword"
