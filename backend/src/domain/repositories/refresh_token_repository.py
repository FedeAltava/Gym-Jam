from abc import ABC, abstractmethod

from backend.src.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def add(self, token: RefreshToken) -> None: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def get_by_id(self, token_id: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: str, replaced_by_id: str | None = None) -> bool:
        """Atomically revoke a still-active token.

        Returns True if the token was revoked by this call, False if it was
        already revoked (lost a concurrent-rotation race). ``replaced_by_id``
        marks a rotation revocation (vs. a logout revocation).
        """
        ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke every token this user has.

        Also clears ``replaced_by_id`` on already-rotated rows so no row keeps
        an open rotation grace window after a family nuke.
        """
        ...

    @abstractmethod
    async def delete_expired(self, user_id: str) -> int:
        """Delete this user's expired tokens. Returns the number of rows removed."""
        ...
