from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_health():
    assert c.get("/health").status_code == 200


def test_usage():
    assert "by_model" in c.get("/usage").json()