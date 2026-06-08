import os


def pytest_configure(config):
    # Runs before Django initialises — must set these here, not at module level.
    os.environ["USE_SQLITE"] = "true"
    os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-prod")
    os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
    os.environ["OLLAMA_MODEL"] = "test-model"
