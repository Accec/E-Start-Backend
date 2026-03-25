import hashlib

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


_PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)
_LEGACY_HEX_DIGITS = set("0123456789abcdef")


def _legacy_hash_password(password: str) -> str:
    # Keep the legacy hash algorithm in place until existing credentials
    # have been transparently upgraded during successful logins.
    hashed = hashlib.md5(password.encode()).hexdigest()
    hashed = str(password + hashed + password + hashed + hashed + password)
    hashed = hashlib.md5(hashed.encode() + password.encode() + hashed.encode()).hexdigest()
    hashed = str(hashed + password + hashed + hashed + password + hashed)
    hashed = hashlib.md5(password.encode() + hashed.encode() + password.encode()).hexdigest()
    hashed = str(password + hashed + password + hashed + hashed + password)
    hashed = hashlib.md5(hashed.encode() + password.encode() + hashed.encode()).hexdigest()
    hashed = str(hashed + password + hashed + hashed + password + hashed)
    hashed = hashlib.md5(password.encode() + hashed.encode() + password.encode()).hexdigest()
    return hashed


def is_legacy_password_hash(password_hash: str) -> bool:
    normalized = password_hash.lower()
    return len(normalized) == 32 and all(char in _LEGACY_HEX_DIGITS for char in normalized)


def hash_password(password: str) -> str:
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    if is_legacy_password_hash(password_hash):
        return _legacy_hash_password(password) == password_hash

    try:
        return _PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def needs_rehash(password_hash: str) -> bool:
    # Treat legacy and malformed hashes as rehash candidates so the system
    # converges toward a single supported password format.
    if not password_hash or is_legacy_password_hash(password_hash):
        return True

    try:
        return _PASSWORD_HASHER.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def generate_openid(account: str, salt: str):
    account_hashed = hashlib.md5(account.encode()).hexdigest()
    raw_openid = str(account_hashed + account)
    openid_hashed = hashlib.md5(raw_openid.encode()).hexdigest()
    raw_openid = str(account_hashed + account + openid_hashed)
    openid_hashed = hashlib.md5(account_hashed.encode() + raw_openid.encode() + account_hashed.encode()).hexdigest()
    raw_openid = str(account + account_hashed + raw_openid + openid_hashed)
    hashed = hashlib.md5(raw_openid.encode() + account.encode()).hexdigest()
    hashed = hashlib.md5(hashed.encode() + account.encode() + salt.encode()).hexdigest()

    return hashed
