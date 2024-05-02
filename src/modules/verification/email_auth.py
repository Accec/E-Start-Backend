import smtplib
import email
from email.mime.text import MIMEText
from email.header import Header
import random

from utils.constant import EMAIL_VERCODE

class EmailAuth:
    def __init__ (self, host, port, email, password, redis):
        self.host = host
        self.port = port
        self.email = email
        self.password = password
        self.redis = redis
        self.timeout = 3 #分钟

    async def _generate_code(self, length=6):
        return ''.join(random.choices('0123456789', k=length))
    
    async def _get_key(self, email):
        return EMAIL_VERCODE.format(email)

    async def send_verification_code(self, to_email):
        
        if not to_email:
            return False

        key = await self._get_key(to_email)
        
        code = await self._generate_code()
        
        # 创建一个邮件文本对象
        subject = "Your Verification Code"
        body = f"Your verification code is: {code}"
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = self.email
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Message-id'] = email.utils.make_msgid()
        
        # 发送邮件
        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.email, self.password)
                server.sendmail(self.email, [to_email], msg.as_string())

                await self.redis.set(key, code)
                await self.redis.expire(key, self.timeout * 60)

        except Exception as e:
            return False
        
        else:
            return True
    
    async def check(self, email, vercode):

        """
        校验短信验证码是否正确
        """
        key = await self._get_key(email)
        value = await self.redis.get(key)
        if not value or value != vercode:
            return False
        else:
            return True