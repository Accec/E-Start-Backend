import base64
import random
import string
from dataclasses import dataclass

from captcha.image import ImageCaptcha


@dataclass(frozen=True, slots=True)
class CaptchaChallenge:
    text: str
    image_base64: str


class ImageCaptchaService:
    def __init__(self, *, length: int = 4):
        self.length = length

    @staticmethod
    def _generate_text(length: int) -> str:
        charset = string.ascii_letters + string.digits
        return "".join(random.choices(charset, k=length))

    @staticmethod
    def _encode_image(captcha_text: str) -> str:
        image = ImageCaptcha().generate(captcha_text, format="JPEG")
        encoded = base64.b64encode(image.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded}"

    def create_challenge(self, *, length: int | None = None) -> CaptchaChallenge:
        captcha_length = length or self.length
        text = self._generate_text(captcha_length)
        return CaptchaChallenge(text=text, image_base64=self._encode_image(text))
