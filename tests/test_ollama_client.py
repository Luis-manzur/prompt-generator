import pytest
from unittest.mock import patch, MagicMock
import requests as req_lib

from apps.improver.ollama_client import (
    OllamaClient,
    OllamaTimeoutError,
    OllamaUnavailableError,
    OllamaResponseError,
)


@pytest.fixture
def client(settings):
    settings.OLLAMA_HOST = "http://localhost:11434"
    settings.OLLAMA_MODEL = "test-model"
    settings.OLLAMA_TIMEOUT_SECONDS = 5
    return OllamaClient()


class TestOllamaClientHappyPath:
    def test_returns_response_text(self, client):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"response": "  improved text  "}
        with patch("apps.improver.ollama_client.requests.post", return_value=mock_resp):
            result = client.improve("system", "user prompt")
        assert result == "improved text"

    def test_strips_leading_trailing_whitespace(self, client):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"response": "\n\n  answer \n"}
        with patch("apps.improver.ollama_client.requests.post", return_value=mock_resp):
            result = client.improve("sys", "usr")
        assert result == "answer"


class TestOllamaClientErrors:
    def test_timeout_raises_ollama_timeout_error(self, client):
        with patch(
            "apps.improver.ollama_client.requests.post",
            side_effect=req_lib.exceptions.Timeout(),
        ):
            with pytest.raises(OllamaTimeoutError):
                client.improve("sys", "usr")

    def test_connection_error_raises_ollama_unavailable_error(self, client):
        with patch(
            "apps.improver.ollama_client.requests.post",
            side_effect=req_lib.exceptions.ConnectionError("refused"),
        ):
            with pytest.raises(OllamaUnavailableError):
                client.improve("sys", "usr")

    def test_non_200_status_raises_ollama_unavailable_error(self, client):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 500
        with patch("apps.improver.ollama_client.requests.post", return_value=mock_resp):
            with pytest.raises(OllamaUnavailableError):
                client.improve("sys", "usr")

    def test_missing_response_key_raises_ollama_response_error(self, client):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"model": "llama3", "done": True}
        with patch("apps.improver.ollama_client.requests.post", return_value=mock_resp):
            with pytest.raises(OllamaResponseError):
                client.improve("sys", "usr")

    def test_invalid_json_raises_ollama_response_error(self, client):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.side_effect = ValueError("not json")
        with patch("apps.improver.ollama_client.requests.post", return_value=mock_resp):
            with pytest.raises(OllamaResponseError):
                client.improve("sys", "usr")
