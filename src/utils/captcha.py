from functools import wraps
import string
import random
from captcha.image import ImageCaptcha
import base64

def get_captcha():
    char_set = string.ascii_letters
    captcha = random.choices(char_set, k=4)
    return ''.join(captcha)

def get_base64_captcha(captcha: str):
    image = ImageCaptcha()
    image = image.generate(captcha, format='JPEG')
    
    image = f"data:image/jpeg;base64,{base64.b64encode(image.getvalue()).decode()}"
    return image

def verify_captcha():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status
            jwt_token = request.token
            is_authorized = decode_jwt(jwt_token)

            if is_authorized:
                # the user is authorized.
                # run the handler method and return the response
                request.ctx.user = is_authorized
                response = await f(request, *args, **kwargs)
                return response
            else:
                # the user is not authorized.
                return http_response(AuthorizedError.code, AuthorizedError.msg)
        return decorated_function
    return decorator