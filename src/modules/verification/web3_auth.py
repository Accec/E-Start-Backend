from web3 import Web3
from eth_account.messages import encode_defunct
from hexbytes import HexBytes

import uuid
w3 = Web3()

account = w3.eth.account.from_key("0x2e2d79d99e16516977a1d57301c09dcf316919b0ee628111db63b07d8df187d4")


message= encode_defunct(text="6875972781")
print (account.address)
print (account.sign_message(message))
print (message)
address = w3.eth.account.recover_message(message, signature=HexBytes("0x7bbdd661acb8db52635510caf733deee2f50c370b4310bb94a0a0a93a611aac53226731d88d91f163d55afe9e64b3dbd9f62ba3ca901bbd66882c0aed23cc9841b"))
print(address)

import random


from utils.constant import WEB3_VERCODE

class Web3Auth:
    def __init__ (self, host, port, email, password, redis):
        self.host = host
        self.port = port
        self.email = email
        self.password = password
        self.redis = redis
        self.timeout = 3 #分钟

    async def _generate_code(self):
        return uuid.uuid4()
    
    async def _get_key(self, email):
        return WEB3_VERCODE.format(email)

    async def send_verification_code(self, to_email):
        
        if not to_email:
            return False

        key = await self._get_key(to_email)
        
        code = await self._generate_code()
        
    
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