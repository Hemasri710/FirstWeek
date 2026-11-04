import json
import time
from collections.abc import AsyncIterator
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import Settings, get_settings
from app.cost import log_call
from app.llm.errors import LLMConfigurationError, LLMUnavailable
from app.llm.factory import create_provider
from app.llm.reliable import AsyncReliableLLM
from app.llm.types import LLMRequest, Message
from app.schemas import ChatAnswer, ChatRequest, QuestionRequest
from app.usage import usage_by_day

app = FastAPI(title="FirstWeek", version="0.2.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]

SYSTEM_PROMPT = (
    "You are FirstWeek, a guide to the FastAPI source code for new joiners. "
    'Reply ONLY with JSON: {"answer": str, "grounded": bool}. '
    "No source context is provided yet. If you are not sure, set grounded=false "
    'and answer exactly "I don\'t know". Never guess about FastAPI internals.'
)


def get_llm(settings: SettingsDep) -> AsyncReliableLLM:
    return create_provider(settings)


LLMDep = Annotated[AsyncReliableLLM, Depends(get_llm)]


@app.get("/")
def say_root():
    return {"service": "FirstWeek", "docs": "/docs", "health": "/health", "ready": "/ready"}


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness: the process is up. Must be fast and must not call the LLM or the DB."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.get("/ready")
def ready(settings: SettingsDep):
    """Readiness: dependencies are reachable. Load balancers and hosts use this."""
    if not settings.database_url:
        return {"status": "ready", "database": "not configured"}
    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return {"status": "ready", "database": "ok"}
    except Exception as exc:  # report, don't crash
        return JSONResponse(status_code=503, content={"status": "not ready", "database": str(exc)[:200]})


def sse(data: dict, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data)}\n\n"


def parse_answer(text: str) -> tuple[str, bool]:
    """Model JSON reply -> (answer, grounded). Anything unparseable = refuse."""
    try:
        cleaned = text.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
        return str(data.get("answer", "I don't know")), bool(data.get("grounded", False))
    except Exception:
        return "I don't know", False


@app.post("/chat", response_model=ChatAnswer)
async def chat(request: QuestionRequest, settings: SettingsDep, provider: LLMDep):
    model = settings.llm_model
    llm_request = LLMRequest(
        messages=(
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=request.question),
        ),
        model=model,
    )
    start = time.perf_counter()
    text, usage, ok, error_message = "", None, True, ""
    try:
        async for chunk in provider.stream(llm_request):
            text += chunk.text
            if chunk.usage is not None:
                usage = chunk.usage
    except (LLMUnavailable, LLMConfigurationError) as error:
        ok = False
        error_message = str(error)
    latency_ms = (time.perf_counter() - start) * 1000
    log_call(
        settings.cost_log_path,
        provider=settings.llm_provider,
        model=model,
        usage=usage or {"input_tokens": 0, "output_tokens": 0, "estimated": False},
        latency_ms=latency_ms,
        price_in_per_m=settings.price_input_per_million,
        price_out_per_m=settings.price_output_per_million,
        ok=ok,
        fallback_used=False,
    )
    if not ok:
        return JSONResponse(status_code=503, content={"detail": f"All models failed: {error_message}"})
    answer, grounded = parse_answer(text)
    return ChatAnswer(answer=answer, grounded=grounded, model=model, latency_ms=int(latency_ms))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, settings: SettingsDep, provider: LLMDep) -> StreamingResponse:
    model = request.model or settings.llm_model
    llm_request = LLMRequest(
        messages=tuple(Message(role=m.role, content=m.content) for m in request.messages),
        model=model,
    )

    async def event_stream() -> AsyncIterator[str]:
        usage = None
        start = time.perf_counter()
        ok = True
        try:
            async for chunk in provider.stream(llm_request):
                if chunk.text:
                    yield sse({"delta": chunk.text})
                if chunk.usage is not None:
                    usage = chunk.usage
        except (LLMUnavailable, LLMConfigurationError) as error:
            ok = False
            yield sse({"error": str(error)}, event="error")

        latency_ms = (time.perf_counter() - start) * 1000
        usage_data = usage or {"input_tokens": 0, "output_tokens": 0, "estimated": False}
        record = log_call(
            settings.cost_log_path,
            provider=settings.llm_provider,
            model=model,
            usage=usage_data,
            latency_ms=latency_ms,
            price_in_per_m=settings.price_input_per_million,
            price_out_per_m=settings.price_output_per_million,
            ok=ok,
            fallback_used=False,
        )
        if hasattr(usage_data, "__dict__"):
            usage_data = usage_data.__dict__
        yield sse({"usage": usage_data, "cost_usd": record["cost_usd"]}, event="done")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/usage")
def usage(settings: SettingsDep) -> dict:
    """Calls, tokens and cost per day (UTC) from the cost log."""
    return usage_by_day(settings.cost_log_path)
