import bcrypt

# Pre-computed dummy hash used to perform a constant-time password check when
# the requested user does not exist, preventing user-enumeration via timing.
DUMMY_HASH: str = bcrypt.hashpw(b"dummy-timing-protection", bcrypt.gensalt(rounds=12)).decode()


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
