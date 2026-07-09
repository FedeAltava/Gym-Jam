"""Tests for RegisterUserUseCase."""
from __future__ import annotations

from typing import Any

import pytest
from returns.result import Failure, Success

from backend.src.application.commands import RegisterUserCommand
from backend.src.application.errors import DomainViolationError
from backend.src.application.use_cases.register_user import RegisterUserUseCase
from backend.src.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self.saved: list[Any] = []
        self.find_calls: list[str] = []

    async def save(self, user: Any) -> None:
        self._store[user.id] = user
        self.saved.append(user)

    async def find_by_email(self, email: str) -> Any | None:
        self.find_calls.append(email)
        return next((u for u in self._store.values() if u.email == email), None)

    async def find_by_id(self, user_id: str) -> Any | None:
        return self._store.get(user_id)


class _FakeUser:
    """Minimal stand-in for a domain user entity."""

    def __init__(self, id: str, email: str, hashed_password: str) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password


def _make_use_case(repo: InMemoryUserRepository) -> RegisterUserUseCase:
    def _create_user(user_id: str, email: str, hashed_password: str) -> _FakeUser:
        return _FakeUser(id=user_id, email=email, hashed_password=hashed_password)

    def _hash(raw: str) -> str:
        return f"hashed({raw})"

    return RegisterUserUseCase(
        user_repo=repo,
        create_user=_create_user,
        hash_password=_hash,
    )


# 1. Happy path
async def test_register_user_happy_path() -> None:
    repo = InMemoryUserRepository()
    uc = _make_use_case(repo)

    result = await uc.execute(RegisterUserCommand(email="alice@example.com", password="secret123"))

    assert isinstance(result, Success)
    user = result.unwrap()
    assert user.email == "alice@example.com"
    assert repo.find_calls == ["alice@example.com"]
    assert len(repo.saved) == 1


# 2. Duplicate email
async def test_register_user_duplicate_email_returns_failure() -> None:
    repo = InMemoryUserRepository()
    uc = _make_use_case(repo)

    await uc.execute(RegisterUserCommand(email="alice@example.com", password="first"))
    repo.saved.clear()  # reset saved tracker for the second call check

    result = await uc.execute(RegisterUserCommand(email="alice@example.com", password="second"))

    assert isinstance(result, Failure)
    assert isinstance(result.failure(), DomainViolationError)
    assert "already registered" in result.failure().message
    # save must NOT be called for the duplicate attempt
    assert len(repo.saved) == 0


# 3. Password is hashed before save
async def test_register_user_password_is_hashed_before_save() -> None:
    repo = InMemoryUserRepository()
    raw = "my-plain-password"

    hashed_received: list[str] = []

    def _create_user(user_id: str, email: str, hashed_password: str) -> _FakeUser:
        hashed_received.append(hashed_password)
        return _FakeUser(id=user_id, email=email, hashed_password=hashed_password)

    uc = RegisterUserUseCase(
        user_repo=repo,
        create_user=_create_user,
        hash_password=lambda p: f"hashed({p})",
    )

    await uc.execute(RegisterUserCommand(email="bob@example.com", password=raw))

    assert len(hashed_received) == 1
    assert hashed_received[0] == f"hashed({raw})"
    assert hashed_received[0] != raw


# 4. create_user receives correct args
async def test_register_user_create_user_receives_correct_args() -> None:
    repo = InMemoryUserRepository()
    captured: list[tuple[str, str, str]] = []

    def _create_user(user_id: str, email: str, hashed_password: str) -> _FakeUser:
        captured.append((user_id, email, hashed_password))
        return _FakeUser(id=user_id, email=email, hashed_password=hashed_password)

    uc = RegisterUserUseCase(
        user_repo=repo,
        create_user=_create_user,
        hash_password=lambda p: f"hashed({p})",
    )

    await uc.execute(RegisterUserCommand(email="carol@example.com", password="pw"))

    assert len(captured) == 1
    uid, email, hashed = captured[0]
    assert uid != ""
    assert email == "carol@example.com"
    assert hashed == "hashed(pw)"


# 5. UUID is generated per call — two registrations produce different IDs
async def test_register_user_uuid_is_unique_per_call() -> None:
    repo = InMemoryUserRepository()
    ids: list[str] = []

    def _create_user(user_id: str, email: str, hashed_password: str) -> _FakeUser:
        ids.append(user_id)
        return _FakeUser(id=user_id, email=email, hashed_password=hashed_password)

    uc = RegisterUserUseCase(
        user_repo=repo,
        create_user=_create_user,
        hash_password=lambda p: p,
    )

    await uc.execute(RegisterUserCommand(email="dave@example.com", password="pw1"))
    await uc.execute(RegisterUserCommand(email="eve@example.com", password="pw2"))

    assert len(ids) == 2
    assert ids[0] != ids[1]
