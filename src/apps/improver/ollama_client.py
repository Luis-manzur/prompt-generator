import requests
from django.conf import settings


class OllamaError(Exception):
    pass


class OllamaTimeoutError(OllamaError):
    pass


class OllamaUnavailableError(OllamaError):
    pass


class OllamaResponseError(OllamaError):
    pass


class OllamaClient:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    def improve(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout}s"
            )
        except requests.exceptions.ConnectionError as exc:
            raise OllamaUnavailableError(
                f"Cannot connect to Ollama at {self.host}: {exc}"
            )

        if not resp.ok:
            raise OllamaUnavailableError(
                f"Ollama returned HTTP {resp.status_code}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise OllamaResponseError(f"Ollama response is not valid JSON: {exc}")

        if "response" not in data:
            raise OllamaResponseError(
                f"Unexpected Ollama response keys: {list(data.keys())}"
            )

        return data["response"].strip()
