from datetime import UTC, datetime

from backend.src.domain.entities.refresh_token import RefreshToken
from backend.src.domain.repositories.refresh_token_repository import RefreshTokenRepository


class InMemoryRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, tokens: list[RefreshToken] | None = None) -> None:
        self._store: dict[str, RefreshToken] = {t.id: t for t in (tokens or [])}

    async def add(self, token: RefreshToken) -> None:
        self._store[token.id] = token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._store.values() if t.token_hash == token_hash), None)

    async def get_by_id(self, token_id: str) -> RefreshToken | None:
        return self._store.get(token_id)

    async def revoke(self, token_id: str, replaced_by_id: str | None = None) -> bool:
        token = self._store.get(token_id)
        if token is None or token.revoked_at is not None:
            return False
        token.revoked_at = datetime.now(UTC)
        token.replaced_by_id = replaced_by_id
        return True

    async def revoke_all_for_user(self, user_id: str) -> None:
        now = datetime.now(UTC)
        for token in self._store.values():
            if token.user_id == user_id:
                if token.revoked_at is None:
                    token.revoked_at = now
                # Family nuke also closes rotation grace windows.
                token.replaced_by_id = None

    async def delete_expired(self, user_id: str) -> int:
        now = datetime.now(UTC)
        expired_ids = [
            t.id for t in self._store.values() if t.user_id == user_id and t.expires_at < now
        ]
        for token_id in expired_ids:
            del self._store[token_id]
        return len(expired_ids)

    # Test helpers
    def peek(self, token_id: str) -> RefreshToken | None:
        return self._store.get(token_id)

    def all_tokens(self) -> list[RefreshToken]:
        return list(self._store.values())
