
from tests.factories import make_contact


class TestContactSubmission:
    async def test_submit_contact(self, client):
        resp = await client.post("/api/contacts", json=make_contact())
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ok"
        assert "id" in data

    async def test_submit_with_honeypot(self, client):
        """Honeypot field filled — silently drop."""
        data = make_contact(website="spam")
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 201
        assert resp.json()["status"] == "ok"
        assert "id" not in resp.json()

    async def test_submit_invalid_phone(self, client):
        data = make_contact(phone="not-a-phone!!!")
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 422

    async def test_submit_empty_name(self, client):
        data = make_contact(name="")
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 422

    async def test_submit_html_stripped(self, client):
        data = make_contact(message="Hello <script>alert('xss')</script> world")
        resp = await client.post("/api/contacts", json=data)
        assert resp.status_code == 201


class TestContactAdmin:
    async def test_list_contacts(self, client, auth_headers):
        await client.post("/api/contacts", json=make_contact())
        resp = await client.get("/api/contacts", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_filter_unprocessed(self, client, auth_headers):
        await client.post("/api/contacts", json=make_contact())
        resp = await client.get("/api/contacts?is_processed=false", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["is_processed"] is False

    async def test_process_contact(self, client, auth_headers):
        create = await client.post("/api/contacts", json=make_contact())
        contact_id = create.json()["id"]
        resp = await client.patch(
            f"/api/contacts/{contact_id}/process", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["is_processed"] is True
