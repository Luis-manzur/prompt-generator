import pytest
from unittest.mock import patch

from apps.improver.ollama_client import OllamaTimeoutError, OllamaUnavailableError

IMPROVE_URL = "/api/improve/"


@pytest.mark.django_db
class TestImproveNoProject:
    def test_happy_path_returns_expected_fields(self, api_client):
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.return_value = "Summarise the report in 3 bullets."
            resp = api_client.post(
                IMPROVE_URL,
                {"prompt": "can you please summarise the report for me in some bullet points"},
                format="json",
            )
        assert resp.status_code == 200
        data = resp.json()
        for field in ("improved_prompt", "raw_tokens", "improved_tokens", "token_delta", "job_id", "model_used"):
            assert field in data
        assert data["model_used"] == "test-model"

    def test_token_delta_equals_improved_minus_raw(self, api_client):
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.return_value = "Fix auth bug."
            resp = api_client.post(
                IMPROVE_URL,
                {"prompt": "I need you to please go ahead and fix the authentication bug in the login flow"},
                format="json",
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_delta"] == data["improved_tokens"] - data["raw_tokens"]

    def test_missing_prompt_returns_400(self, api_client):
        resp = api_client.post(IMPROVE_URL, {}, format="json")
        assert resp.status_code == 400

    def test_whitespace_only_prompt_returns_400(self, api_client):
        resp = api_client.post(IMPROVE_URL, {"prompt": "   "}, format="json")
        assert resp.status_code == 400

    def test_nonexistent_project_id_returns_404(self, api_client):
        with patch("apps.improver.views.OllamaClient"):
            resp = api_client.post(
                IMPROVE_URL,
                {"prompt": "test prompt", "project_id": 99999},
                format="json",
            )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestImproveWithProject:
    def test_project_context_included_in_system_prompt(
        self, api_client, sample_project, sample_files
    ):
        captured = {}

        def fake_improve(system_prompt, user_prompt):
            captured["system_prompt"] = system_prompt
            return "Improved: " + user_prompt

        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.side_effect = fake_improve
            resp = api_client.post(
                IMPROVE_URL,
                {"prompt": "write a function", "project_id": sample_project["id"]},
                format="json",
            )

        assert resp.status_code == 200
        assert (
            "instructions.md" in captured["system_prompt"]
            or "style.md" in captured["system_prompt"]
        )


@pytest.mark.django_db
class TestImproveOllamaErrors:
    def test_timeout_returns_503(self, api_client):
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.side_effect = OllamaTimeoutError("timed out")
            resp = api_client.post(IMPROVE_URL, {"prompt": "hello"}, format="json")
        assert resp.status_code == 503
        assert "error" in resp.json()

    def test_unavailable_returns_503(self, api_client):
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.side_effect = OllamaUnavailableError("down")
            resp = api_client.post(IMPROVE_URL, {"prompt": "hello"}, format="json")
        assert resp.status_code == 503

    def test_job_saved_on_success_with_completed_status(self, api_client):
        from apps.improver.models import PromptJob
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.return_value = "Better prompt."
            resp = api_client.post(IMPROVE_URL, {"prompt": "original"}, format="json")
        assert resp.status_code == 200
        job = PromptJob.objects.get(pk=resp.json()["job_id"])
        assert job.status == PromptJob.STATUS_COMPLETED
        assert job.improved_prompt == "Better prompt."

    def test_job_saved_on_failure_with_error_field(self, api_client):
        from apps.improver.models import PromptJob
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.side_effect = OllamaUnavailableError("connection refused")
            api_client.post(IMPROVE_URL, {"prompt": "fail me"}, format="json")
        job = PromptJob.objects.filter(status=PromptJob.STATUS_FAILED).first()
        assert job is not None
        assert "connection refused" in job.error


@pytest.mark.django_db
class TestPromptJobDetail:
    def test_get_job_detail_returns_full_record(self, api_client):
        with patch("apps.improver.views.OllamaClient") as MockClient:
            MockClient.return_value.improve.return_value = "Terse prompt."
            create_resp = api_client.post(
                IMPROVE_URL, {"prompt": "long rambling prompt"}, format="json"
            )
        assert create_resp.status_code == 200
        job_id = create_resp.json()["job_id"]

        detail = api_client.get(f"/api/improve/{job_id}/")
        assert detail.status_code == 200
        data = detail.json()
        assert data["id"] == job_id
        assert data["raw_prompt"] == "long rambling prompt"
        assert data["status"] == "completed"

    def test_get_nonexistent_job_returns_404(self, api_client):
        resp = api_client.get("/api/improve/99999/")
        assert resp.status_code == 404
