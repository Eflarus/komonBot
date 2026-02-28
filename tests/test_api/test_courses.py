
from tests.factories import make_course


class TestCoursesCRUD:
    async def test_create_course(self, client, auth_headers):
        resp = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Course"
        assert data["status"] == "draft"

    async def test_list_courses(self, client, auth_headers):
        await client.post("/api/courses", json=make_course(), headers=auth_headers)
        resp = await client.get("/api/courses", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_get_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.get(f"/api/courses/{course_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == course_id

    async def test_update_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.patch(
            f"/api/courses/{course_id}",
            json={"title": "Updated Course"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Course"

    async def test_delete_draft_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.delete(f"/api/courses/{course_id}", headers=auth_headers)
        assert resp.status_code == 204


class TestCourseLifecycle:
    async def test_publish_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.post(f"/api/courses/{course_id}/publish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    async def test_unpublish_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        await client.post(f"/api/courses/{course_id}/publish", headers=auth_headers)
        resp = await client.post(f"/api/courses/{course_id}/unpublish", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    async def test_cannot_delete_published(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        await client.post(f"/api/courses/{course_id}/publish", headers=auth_headers)
        resp = await client.delete(f"/api/courses/{course_id}", headers=auth_headers)
        assert resp.status_code == 400


class TestCourseRBAC:
    async def test_editor_can_create_course(self, client, auth_headers, editor_headers):
        resp = await client.post("/api/courses", json=make_course(), headers=editor_headers)
        assert resp.status_code == 201

    async def test_editor_cannot_delete_course(self, client, auth_headers, editor_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.delete(f"/api/courses/{course_id}", headers=editor_headers)
        assert resp.status_code == 403

    async def test_admin_can_delete_course(self, client, auth_headers):
        create = await client.post("/api/courses", json=make_course(), headers=auth_headers)
        course_id = create.json()["id"]
        resp = await client.delete(f"/api/courses/{course_id}", headers=auth_headers)
        assert resp.status_code == 204
