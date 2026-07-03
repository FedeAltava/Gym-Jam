"""RefreshToken entity — opaque token reference stored by hash only."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:
    id: str
    user_id: str
    token_hash: str  # sha256 hex of the raw token — raw value is never stored
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    # Set when the token was revoked by rotation — points at the token that
    # replaced it. None means the token was revoked by logout (or never revoked).
    replaced_by_id: str | None = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def was_rotated(self) -> bool:
        """True when this token was revoked because a rotation replaced it."""
        return self.replaced_by_id is not None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now
