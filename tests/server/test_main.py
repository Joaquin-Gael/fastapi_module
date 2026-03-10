import pytest
from fastapi.testclient import TestClient
from server.core.main import app

client = TestClient(app)


def test_docs_endpoint():
    response = client.get("/scalar/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_admin_endpoint():
    response = client.get("/admin/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_auth_endpoint_structure():
    response = client.get("/auth/")
    assert response.status_code == 200


def test_user_endpoint_structure():
    response = client.get("/user/")
    assert response.status_code == 200


def test_logs_endpoint_with_form():
    response = client.post(
        "/admin/logs", data={"offset": "0", "limit": "10", "word_key": ""}
    )
    assert response.status_code in [200, 500]


def test_nonexistent_endpoint():
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_api_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
