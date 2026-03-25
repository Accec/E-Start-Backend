import random
import smtplib
from email.message import EmailMessage

from core.constants import EMAIL_VERIFICATION_CODE_KEY


class EmailCodeVerifier:
    def __init__(self, *, host, port, sender_email, sender_password, redis_client, ttl_minutes=3):
        self.host = host
        self.port = port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.redis = redis_client
        self.ttl_minutes = ttl_minutes

    @staticmethod
    def _normalize_email(email_address: str) -> str:
        return email_address.strip().lower()

    @staticmethod
    def _generate_code(length=6) -> str:
        return "".join(random.choices("0123456789", k=length))

    def _build_key(self, email_address: str) -> str:
        return EMAIL_VERIFICATION_CODE_KEY.format(self._normalize_email(email_address))

    def _build_message(self, recipient_email: str, code: str) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self.sender_email
        message["To"] = recipient_email
        message["Subject"] = "Your Verification Code"
        message.set_content(f"Your verification code is: {code}")
        return message

    async def send_code(self, recipient_email: str) -> bool:
        normalized_email = self._normalize_email(recipient_email)
        if not normalized_email:
            return False

        key = self._build_key(normalized_email)
        code = self._generate_code()
        message = self._build_message(normalized_email, code)

        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
                await self.redis.set(key, code)
                await self.redis.expire(key, self.ttl_minutes * 60)
        except Exception:
            return False

        return True

    async def verify_code(self, email_address: str, verification_code: str) -> bool:
        key = self._build_key(email_address)
        value = await self.redis.get(key)
        return bool(value and value == verification_code)
