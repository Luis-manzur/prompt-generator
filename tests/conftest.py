import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_project(api_client):
    resp = api_client.post(
        "/api/projects/",
        {"name": "test-project", "description": "A test project"},
        format="json",
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
def sample_files(api_client, sample_project):
    pid = sample_project["id"]
    f1 = api_client.post(
        f"/api/projects/{pid}/files/",
        {"filename": "instructions.md", "content": "# Instructions\n\nBe concise."},
        format="json",
    )
    f2 = api_client.post(
        f"/api/projects/{pid}/files/",
        {"filename": "style.md", "content": "# Style\n\nUse plain English."},
        format="json",
    )
    assert f1.status_code == 201
    assert f2.status_code == 201
    return [f1.json(), f2.json()]
