import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs

import structlog
from pydantic import BaseModel

from src.exceptions import AuthError

logger = structlog.get_logger()

INIT_DATA_MAX_AGE = 300  # seconds (5 min)
AUTH_FAILED_MSG = "Authentication failed"


class TelegramUser(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


def validate_init_data(init_data: str, bot_token: str) -> TelegramUser:
    """Validate Telegram WebApp initData HMAC signature and extract user."""
    if not init_data:
        raise AuthError(AUTH_FAILED_MSG)

    parsed = parse_qs(init_data)

    # Check required fields
    if "hash" not in parsed or "auth_date" not in parsed or "user" not in parsed:
        raise AuthError(AUTH_FAILED_MSG)

    # 1. Check auth_date freshness
    try:
        auth_date = int(parsed["auth_date"][0])
    except (ValueError, IndexError):
        raise AuthError(AUTH_FAILED_MSG)

    if time.time() - auth_date > INIT_DATA_MAX_AGE:
        raise AuthError(AUTH_FAILED_MSG)

    # 2. Verify HMAC-SHA256
    received_hash = parsed["hash"][0]
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    check_items = sorted(
        (k, v[0]) for k, v in parsed.items() if k != "hash"
    )
    check_string = "\n".join(f"{k}={v}" for k, v in check_items)
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise AuthError(AUTH_FAILED_MSG)

    # 3. Extract user
    try:
        user_data = json.loads(parsed["user"][0])
        return TelegramUser.model_validate(user_data)
    except (json.JSONDecodeError, KeyError, IndexError):
        raise AuthError(AUTH_FAILED_MSG)
