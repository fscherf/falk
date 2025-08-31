import secrets
import base64


def get_random_key(length=32):
    return base64.urlsafe_b64encode(
        secrets.token_bytes(length),
    ).decode()
