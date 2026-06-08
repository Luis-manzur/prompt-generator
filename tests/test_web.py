import pytest
from unittest.mock import patch

from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.projects.models import Project, ProjectFile
from apps.improver.models import PromptJob


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestImprovePage:
    def test_page_renders(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Improve a prompt" in resp.content

    def test_improve_returns_result_partial(self, client):
        with patch("apps.web.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.return_value = "Summarise in 3 bullets."
            resp = client.post("/improve/", {"prompt": "please summarise this for me"})
        assert resp.status_code == 200
        assert b"Improved prompt" in resp.content
        assert b"Summarise in 3 bullets." in resp.content
        assert PromptJob.objects.filter(status="completed").count() == 1

    def test_empty_prompt_shows_error(self, client):
        resp = client.post("/improve/", {"prompt": "   "})
        assert resp.status_code == 200
        assert b"Prompt is required." in resp.content

    def test_ollama_failure_renders_error(self, client):
        from apps.improver.ollama_client import OllamaUnavailableError
        with patch("apps.web.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.side_effect = OllamaUnavailableError("down")
            resp = client.post("/improve/", {"prompt": "fix the bug"})
        assert resp.status_code == 200
        assert b"Ollama unavailable" in resp.content
        assert PromptJob.objects.filter(status="failed").count() == 1


@pytest.mark.django_db
class TestProjects:
    def test_create_project(self, client):
        resp = client.post("/projects/", {"name": "alpha", "description": "x"})
        assert resp.status_code == 200
        assert Project.objects.filter(name="alpha").exists()
        assert b"alpha" in resp.content

    def test_duplicate_name_ignored(self, client):
        Project.objects.create(name="alpha")
        resp = client.post("/projects/", {"name": "alpha"})
        assert resp.status_code == 200
        assert Project.objects.filter(name="alpha").count() == 1

    def test_delete_project(self, client):
        p = Project.objects.create(name="alpha")
        resp = client.post(f"/projects/{p.id}/delete/")
        assert resp.status_code == 200
        assert not Project.objects.filter(pk=p.id).exists()


@pytest.mark.django_db
class TestFiles:
    def test_upload_file(self, client):
        p = Project.objects.create(name="alpha")
        upload = SimpleUploadedFile("ctx.md", b"# Hello", content_type="text/markdown")
        resp = client.post(f"/projects/{p.id}/files/", {"file": upload})
        assert resp.status_code == 200
        assert ProjectFile.objects.filter(project=p, filename="ctx.md").exists()
        assert b"ctx.md" in resp.content

    def test_reupload_bumps_version(self, client):
        p = Project.objects.create(name="alpha")
        ProjectFile.objects.create(project=p, filename="ctx.md", content="old")
        upload = SimpleUploadedFile("ctx.md", b"new", content_type="text/markdown")
        client.post(f"/projects/{p.id}/files/", {"file": upload})
        pf = ProjectFile.objects.get(project=p, filename="ctx.md")
        assert pf.version == 2
        assert pf.content == "new"

    def test_delete_file(self, client):
        p = Project.objects.create(name="alpha")
        pf = ProjectFile.objects.create(project=p, filename="ctx.md", content="x")
        resp = client.post(f"/projects/{p.id}/files/{pf.id}/delete/")
        assert resp.status_code == 200
        assert not ProjectFile.objects.filter(pk=pf.id).exists()
