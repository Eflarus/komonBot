
from tests.conftest import make_init_data
from tests.factories import make_event


class TestEventsCRUD:
    async def test_create_event(self, client, auth_headers):
        resp = await client.post("/api/events", json=make_event(), headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Event"
        assert data["status"] == "draft"

    async def test_list_events(self, client, auth_headers):
        await client.post("/api/events", json=make_event(), headers=auth_headers)
        resp = await client.get("/api/events", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.get(f"/api/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == event_id

    async def test_update_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.patch(
            f"/api/events/{event_id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    async def test_delete_draft_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_get_nonexistent_event(self, client, auth_headers):
        resp = await client.get("/api/events/9999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_filter_by_status(self, client, auth_headers):
        await client.post("/api/events", json=make_event(), headers=auth_headers)
        resp = await client.get("/api/events?status=draft", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "draft"

    async def test_search_events(self, client, auth_headers):
        await client.post(
            "/api/events", json=make_event(title="Unique Name"), headers=auth_headers
        )
        resp = await client.get("/api/events?search=Unique", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


class TestEventLifecycle:
    async def test_publish_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.post(f"/api/events/{event_id}/publish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    async def test_publish_incomplete_event(self, client, auth_headers):
        create = await client.post(
            "/api/events",
            json={"title": "No Location"},
            headers=auth_headers,
        )
        event_id = create.json()["id"]
        resp = await client.post(f"/api/events/{event_id}/publish", headers=auth_headers)
        assert resp.status_code == 400

    async def test_unpublish_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        await client.post(f"/api/events/{event_id}/publish", headers=auth_headers)
        resp = await client.post(f"/api/events/{event_id}/unpublish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    async def test_cancel_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        await client.post(f"/api/events/{event_id}/publish", headers=auth_headers)
        resp = await client.post(f"/api/events/{event_id}/cancel", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_cannot_delete_published(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        await client.post(f"/api/events/{event_id}/publish", headers=auth_headers)
        resp = await client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 400


class TestEventValidation:
    async def test_create_with_null_optional_fields(self, client, auth_headers):
        """Webapp sends null for empty date/time/ticket_link — should not 422."""
        resp = await client.post(
            "/api/events",
            json={
                "title": "Minimal Event",
                "event_date": None,
                "event_time": None,
                "ticket_link": None,
                "order": 0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Minimal Event"
        assert data["event_date"] is None
        assert data["event_time"] is None
        assert data["ticket_link"] is None

    async def test_create_with_only_title(self, client, auth_headers):
        """Minimum valid payload: just title."""
        resp = await client.post(
            "/api/events",
            json={"title": "Title Only"},
            headers=auth_headers,
        )
        assert resp.status_code == 201

    async def test_create_rejects_empty_title(self, client, auth_headers):
        resp = await client.post(
            "/api/events",
            json={"title": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestEventAuth:
    async def test_no_auth_header(self, client):
        resp = await client.get("/api/events")
        assert resp.status_code == 422  # missing header

    async def test_invalid_auth(self, client):
        resp = await client.get(
            "/api/events", headers={"X-Telegram-Init-Data": "invalid"}
        )
        assert resp.status_code == 401

    async def test_non_whitelisted_user(self, client):
        init_data = make_init_data(user_id=999999999)
        resp = await client.get(
            "/api/events", headers={"X-Telegram-Init-Data": init_data}
        )
        assert resp.status_code == 403


class TestEventRBAC:
    async def test_editor_can_create_event(self, client, auth_headers, editor_headers):
        resp = await client.post("/api/events", json=make_event(), headers=editor_headers)
        assert resp.status_code == 201

    async def test_editor_cannot_delete_event(self, client, auth_headers, editor_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.delete(f"/api/events/{event_id}", headers=editor_headers)
        assert resp.status_code == 403

    async def test_admin_can_delete_event(self, client, auth_headers):
        create = await client.post("/api/events", json=make_event(), headers=auth_headers)
        event_id = create.json()["id"]
        resp = await client.delete(f"/api/events/{event_id}", headers=auth_headers)
        assert resp.status_code == 204
