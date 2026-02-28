
from tests.factories import make_user


class TestUsersCRUD:
    async def test_list_users(self, client, auth_headers):
        resp = await client.get("/api/users", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1  # at least the seeded admin

    async def test_add_user(self, client, auth_headers):
        resp = await client.post("/api/users", json=make_user(), headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["telegram_id"] == 987654321

    async def test_add_duplicate_user(self, client, auth_headers):
        await client.post("/api/users", json=make_user(), headers=auth_headers)
        resp = await client.post("/api/users", json=make_user(), headers=auth_headers)
        assert resp.status_code == 400

    async def test_delete_user(self, client, auth_headers):
        create = await client.post("/api/users", json=make_user(), headers=auth_headers)
        user_id = create.json()["id"]
        resp = await client.delete(f"/api/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_cannot_delete_self(self, client, auth_headers):
        # The admin user (telegram_id=123456789) is already in the list
        resp = await client.get("/api/users", headers=auth_headers)
        admin = next(u for u in resp.json() if u["telegram_id"] == 123456789)
        resp = await client.delete(f"/api/users/{admin['id']}", headers=auth_headers)
        assert resp.status_code == 400

    async def test_delete_nonexistent_user(self, client, auth_headers):
        resp = await client.delete("/api/users/9999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_add_user_has_role(self, client, auth_headers):
        resp = await client.post("/api/users", json=make_user(), headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["role"] == "editor"

    async def test_add_admin_user(self, client, auth_headers):
        data = make_user(role="admin")
        resp = await client.post("/api/users", json=data, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"


class TestUserRoles:
    async def test_editor_cannot_add_user(self, client, editor_headers):
        resp = await client.post(
            "/api/users", json=make_user(telegram_id=555555), headers=editor_headers
        )
        assert resp.status_code == 403

    async def test_editor_cannot_delete_user(self, client, editor_headers, auth_headers):
        create = await client.post("/api/users", json=make_user(), headers=auth_headers)
        user_id = create.json()["id"]
        resp = await client.delete(f"/api/users/{user_id}", headers=editor_headers)
        assert resp.status_code == 403

    async def test_editor_can_list_users(self, client, editor_headers):
        resp = await client.get("/api/users", headers=editor_headers)
        assert resp.status_code == 200

    async def test_editor_can_list_events(self, client, editor_headers):
        resp = await client.get("/api/events", headers=editor_headers)
        assert resp.status_code == 200
