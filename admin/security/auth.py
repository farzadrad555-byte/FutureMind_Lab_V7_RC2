
import hashlib
from admin.security.config import USERNAME, PASSWORD_HASH


def check_login(username, password):

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()

    if username == USERNAME and password_hash == PASSWORD_HASH:
        return True

    return False
