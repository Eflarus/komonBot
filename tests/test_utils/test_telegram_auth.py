import hashlib
import hmac
import json
import time

import pytest

from src.exceptions import AuthError
from src.utils.telegram_auth import TelegramUser, validate_init_data

BOT_TOKEN = "123456:ABC-DEF-test-token"


def _make_init_data(
    user_id=12345,
    auth_date=None,
    bot_token=BOT_TOKEN,
    tamper_hash=False,
):
    user_data = json.dumps({"id": user_id, "first_name": "Test"})
    auth_date = auth_date or str(int(time.time()))

    data_parts = {"auth_date": auth_date, "user": user_data}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_parts.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_value = hmac.new(
        secret_key, check_string.encode(), hashlib.sha256
    ).hexdigest()

    if tamper_hash:
        hash_value = "0" * 64

    parts = [f"{k}={v}" for k, v in data_parts.items()]
    parts.append(f"hash={hash_value}")
    return "&".join(parts)


class TestValidateInitData:
    def test_valid_init_data(self):
        init_data = _make_init_data()
        user = validate_init_data(init_data, BOT_TOKEN)
        assert isinstance(user, TelegramUser)
        assert user.id == 12345

    def test_expired_init_data(self):
        old_time = str(int(time.time()) - 700)
        init_data = _make_init_data(auth_date=old_time)
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_tampered_hash(self):
        init_data = _make_init_data(tamper_hash=True)
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_wrong_bot_token(self):
        init_data = _make_init_data(bot_token="other:token")
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_empty_init_data(self):
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data("", BOT_TOKEN)

    def test_missing_hash(self):
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data("auth_date=123&user={}", BOT_TOKEN)

    def test_missing_user(self):
        with pytest.raises(AuthError, match="Authentication failed"):
            validate_init_data("auth_date=123&hash=abc", BOT_TOKEN)

    def test_all_errors_have_same_message(self):
        """Ensure all error scenarios return the same generic message."""
        cases = [
            ("", BOT_TOKEN),
            ("auth_date=123&user={}", BOT_TOKEN),
            ("auth_date=123&hash=abc", BOT_TOKEN),
            (_make_init_data(tamper_hash=True), BOT_TOKEN),
            (_make_init_data(auth_date=str(int(time.time()) - 700)), BOT_TOKEN),
        ]
        for init_data, token in cases:
            with pytest.raises(AuthError) as exc_info:
                validate_init_data(init_data, token)
            assert exc_info.value.message == "Authentication failed"
