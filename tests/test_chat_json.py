import json

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.llm.fake import FakeProvider
from app.llm.reliable import AsyncReliableLLM
from app.main import app, get_llm


def _client(chunks):
    app.dependency_overrides[get_settings] = lambda: Settings(environment="test")
    app.dependency_overrides[get_llm] = lambda: AsyncReliableLLM(FakeProvider(chunks=chunks))
    return TestClient(app)


def test_chat_returns_structured_json():
    reply = json.dumps({"answer": "Depends resolves sub-dependencies.", "grounded": True})
    try:
        with _client((reply,)) as client:
            body = client.post("/chat", json={"question": "How does Depends work?"}).json()
    finally:
        app.dependency_overrides.clear()
    assert body["grounded"] is True
    assert {"answer", "citations", "grounded", "model", "latency_ms"} <= body.keys()


def test_chat_refuses_when_reply_is_not_json():
    try:
        with _client(("not json at all",)) as client:
            body = client.post("/chat", json={"question": "anything"}).json()
    finally:
        app.dependency_overrides.clear()
    assert body["answer"] == "I don't know"
    assert body["grounded"] is False
