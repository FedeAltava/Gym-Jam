"""Tests for password utilities — RED phase first."""
from backend.src.infrastructure.auth.password import hash_password, verify_password


def test_hash_password_returns_bcrypt_hash() -> None:
    hashed = hash_password("strongpass123")
    assert hashed.startswith("$2b$")
    assert hashed != "strongpass123"


def test_hash_password_different_inputs_produce_different_hashes() -> None:
    h1 = hash_password("password1")
    h2 = hash_password("password2")
    assert h1 != h2


def test_verify_password_correct_password_returns_true() -> None:
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong_password_returns_false() -> None:
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_hash_same_password_twice_produces_different_hashes() -> None:
    # bcrypt uses random salt
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2
    # but both verify
    assert verify_password("same", h1) is True
    assert verify_password("same", h2) is True
