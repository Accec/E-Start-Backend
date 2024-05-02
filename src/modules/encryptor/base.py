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
