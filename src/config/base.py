import base64
import secrets

JwtSecretKey = base64.b64encode(secrets.token_bytes(512)).decode()

#时区设置
Timezone = "UTC"
JwtExpTime = 60 * 60 * 24
