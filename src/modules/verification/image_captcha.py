import string
import random
from captcha.image import ImageCaptcha
import base64

def get_captcha():
    char_set = string.ascii_letters + string.digits
    captcha = random.choices(char_set, k=4)
    return ''.join(captcha)

def get_base64_captcha(captcha: str):
    image = ImageCaptcha()
    image = image.generate(captcha, format='JPEG')
    
    image = f"data:image/jpeg;base64,{base64.b64encode(image.getvalue()).decode()}"
    return image

if __name__ == "__main__":
    captcha = get_captcha()
    print (get_base64_captcha(captcha))