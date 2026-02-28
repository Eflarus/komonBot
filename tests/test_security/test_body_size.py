class TestBodySizeLimit:
    async def test_normal_request_accepted(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_oversized_body_rejected(self, client):
        resp = await client.post(
            "/api/contacts",
            content="x" * (3 * 1024 * 1024),
            headers={"Content-Type": "application/json", "Content-Length": str(3 * 1024 * 1024)},
        )
        assert resp.status_code == 413

    async def test_normal_sized_post_accepted(self, client):
        from tests.factories import make_contact

        resp = await client.post("/api/contacts", json=make_contact())
        assert resp.status_code == 201
