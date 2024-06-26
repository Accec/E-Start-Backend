import hashlib

def hash_password(password: str):
    # Hash the password using MD5
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

def generate_openid(account:str, salt: str):
    # Hash the openid using MD5
    account_hashed = hashlib.md5(account.encode()).hexdigest()
    raw_openid = str(account_hashed + account)
    openid_hashed = hashlib.md5(raw_openid.encode()).hexdigest()
    raw_openid = str(account_hashed + account + openid_hashed)
    openid_hashed = hashlib.md5(account_hashed.encode() + raw_openid.encode() + account_hashed.encode()).hexdigest()
    raw_openid = str(account + account_hashed + raw_openid + openid_hashed)
    hashed = hashlib.md5(raw_openid.encode() + account.encode()).hexdigest()
    hashed = hashlib.md5(hashed.encode() + account.encode() + salt.encode()).hexdigest()

    return hashed