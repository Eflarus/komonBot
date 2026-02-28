from unittest.mock import MagicMock

from src.api.contacts import _get_real_ip


class TestGetRealIp:
    def _make_request(self, headers: dict, client_host: str = "127.0.0.1"):
        request = MagicMock()
        request.headers = headers
        request.client.host = client_host
        return request

    def test_uses_x_forwarded_for_first_ip(self):
        request = self._make_request(
            {"X-Forwarded-For": "203.0.113.1, 10.0.0.1, 127.0.0.1"}
        )
        assert _get_real_ip(request) == "203.0.113.1"

    def test_uses_x_real_ip_when_no_forwarded(self):
        request = self._make_request({"X-Real-IP": "198.51.100.5"})
        assert _get_real_ip(request) == "198.51.100.5"

    def test_x_forwarded_for_takes_precedence(self):
        request = self._make_request(
            {"X-Forwarded-For": "203.0.113.1", "X-Real-IP": "198.51.100.5"}
        )
        assert _get_real_ip(request) == "203.0.113.1"

    def test_falls_back_to_client_host(self):
        request = self._make_request({}, client_host="192.168.1.100")
        assert _get_real_ip(request) == "192.168.1.100"

    def test_strips_whitespace(self):
        request = self._make_request({"X-Forwarded-For": "  203.0.113.1 , 10.0.0.1"})
        assert _get_real_ip(request) == "203.0.113.1"

    def test_handles_no_client(self):
        request = MagicMock()
        request.headers = {}
        request.client = None
        assert _get_real_ip(request) == "unknown"
