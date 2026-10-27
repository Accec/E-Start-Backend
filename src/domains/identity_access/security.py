import datetime
import secrets
import string

from jwt import PyJWT

from infra.security.passwords import generate_openid, hash_password, needs_rehash, verify_password


class PasswordCredentialService:
    def hash_password(self, password: str):
        return hash_password(password)

    def verify_password(self, password: str, password_hash: str):
        return verify_password(password, password_hash)

    def needs_rehash(self, password_hash: str):
        return needs_rehash(password_hash)

    def generate_openid(self, account: str, salt: str):
        return generate_openid(account, salt)

    def generate_password(self, length: int = 12):
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))


class JwtTokenIssuer:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def issue_token(self, user_id: int, exp_seconds: int):
        payload = {
            "user_id": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=exp_seconds),
        }
        return PyJWT().encode(payload, self.secret_key, algorithm="HS256")
