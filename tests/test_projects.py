import pytest


@pytest.mark.django_db
class TestProjectCRUD:
    def test_create_project(self, api_client):
        resp = api_client.post("/api/projects/", {"name": "my-proj"}, format="json")
        assert resp.status_code == 201
        assert resp.json()["name"] == "my-proj"

    def test_create_project_duplicate_name(self, api_client, sample_project):
        resp = api_client.post(
            "/api/projects/", {"name": sample_project["name"]}, format="json"
        )
        assert resp.status_code == 400

    def test_list_projects_empty(self, api_client):
        resp = api_client.get("/api/projects/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_projects_with_data(self, api_client, sample_project):
        resp = api_client.get("/api/projects/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_retrieve_project_includes_files(self, api_client, sample_project, sample_files):
        pid = sample_project["id"]
        resp = api_client.get(f"/api/projects/{pid}/")
        assert resp.status_code == 200
        assert len(resp.json()["files"]) == 2

    def test_retrieve_nonexistent_project(self, api_client):
        resp = api_client.get("/api/projects/99999/")
        assert resp.status_code == 404

    def test_delete_project_cascades_files(self, api_client, sample_project, sample_files):
        pid = sample_project["id"]
        assert api_client.delete(f"/api/projects/{pid}/").status_code == 204
        assert api_client.get(f"/api/projects/{pid}/").status_code == 404


@pytest.mark.django_db
class TestProjectFileCRUD:
    def test_upload_new_file_returns_201_version_1(self, api_client, sample_project):
        pid = sample_project["id"]
        resp = api_client.post(
            f"/api/projects/{pid}/files/",
            {"filename": "context.md", "content": "# Context"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["version"] == 1
        assert resp.json()["filename"] == "context.md"

    def test_upload_existing_file_upserts_and_increments_version(
        self, api_client, sample_project, sample_files
    ):
        pid = sample_project["id"]
        filename = sample_files[0]["filename"]
        resp = api_client.post(
            f"/api/projects/{pid}/files/",
            {"filename": filename, "content": "# Updated content"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["version"] == 2
        assert resp.json()["content"] == "# Updated content"

    def test_list_files(self, api_client, sample_project, sample_files):
        pid = sample_project["id"]
        resp = api_client.get(f"/api/projects/{pid}/files/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_retrieve_file(self, api_client, sample_project, sample_files):
        pid = sample_project["id"]
        fid = sample_files[0]["id"]
        resp = api_client.get(f"/api/projects/{pid}/files/{fid}/")
        assert resp.status_code == 200
        assert resp.json()["id"] == fid

    def test_delete_file(self, api_client, sample_project, sample_files):
        pid = sample_project["id"]
        fid = sample_files[0]["id"]
        assert api_client.delete(f"/api/projects/{pid}/files/{fid}/").status_code == 204
        assert api_client.get(f"/api/projects/{pid}/files/{fid}/").status_code == 404

    def test_upload_missing_filename(self, api_client, sample_project):
        pid = sample_project["id"]
        resp = api_client.post(
            f"/api/projects/{pid}/files/",
            {"content": "no filename here"},
            format="json",
        )
        assert resp.status_code == 400
