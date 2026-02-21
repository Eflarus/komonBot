import time

import jwt


def make_ghost_jwt(admin_api_key: str) -> str:
    """Generate short-lived JWT for Ghost Admin API auth (HS256, 5 min expiry).

    admin_api_key format: "id:secret" (hex-encoded secret)
    """
    key_id, secret_hex = admin_api_key.split(":")
    secret = bytes.fromhex(secret_hex)

    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + 300,  # 5 min
        "aud": "/admin/",
    }
    headers = {
        "alg": "HS256",
        "typ": "JWT",
        "kid": key_id,
    }

    return jwt.encode(payload, secret, algorithm="HS256", headers=headers)
