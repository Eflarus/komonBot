import time

from tests.factories import make_contact


class TestTimingCheck:
    async def test_submit_without_timestamp_accepted(self, client):
        """Submissions without form_ts are accepted (backwards compatible)."""
        resp = await client.post("/api/contacts", json=make_contact())
        assert resp.status_code == 201
        assert "id" in resp.json()

    async def test_submit_with_valid_timestamp_accepted(self, client):
        """Submissions with form_ts older than 3 seconds are accepted."""
        data = make_contact(form_ts=int(time.time()) - 10)
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 201
        assert "id" in resp.json()

    async def test_submit_too_fast_silently_dropped(self, client):
        """Submissions with form_ts less than 3 seconds ago are silently dropped."""
        data = make_contact(form_ts=int(time.time()))
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 201
        assert resp.json()["status"] == "ok"
        assert "id" not in resp.json()
