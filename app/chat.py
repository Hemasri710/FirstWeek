import json
import os
import time
from pathlib import Path

import litellm
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import usage

# Read the .env in the project root. override=False keeps values that are already
# set (for example by pytest or by Render), so tests are not changed by your local .env.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

# Hide litellm's long "Give Feedback / Get Help" messages
litellm.suppress_debug_info = True

router = APIRouter()

SYSTEM = (
    "You are FirstWeek, a guide to the FastAPI source code for new joiners. "
    'Reply ONLY with JSON: {"answer": str, "grounded": bool}. '
    "No source context is provided yet. If you are not sure, set grounded=false "
    'and answer exactly "I don\'t know". Never guess about FastAPI internals.'
)


class ChatRequest(BaseModel):
    question: str


class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    grounded: bool
    model: str
    latency_ms: int


def _models():
    """Primary model first, then the fallback model."""
    return [m for m in (os.getenv("PRIMARY_MODEL"), os.getenv("FALLBACK_MODEL")) if m]


def _messages(q):
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": q},
    ]


def _call(q, stream=False):
    last = None
    for m in _models():
        print("trying model:", m)
        try:
            return m, litellm.completion(
                model=m,
                messages=_messages(q),
                timeout=20,
                num_retries=2,
                stream=stream,
            )
        except Exception as e:
            print("model failed:", m, "->", e)
            last = e
    raise HTTPException(503, f"All models failed: {last}")


def _parse(text):
    try:
        t = text.strip().removeprefix("```json").removesuffix("```").strip()
        d = json.loads(t)
        return str(d.get("answer", "I don't know")), bool(d.get("grounded", False))
    except Exception:
        return "I don't know", False


def _record(model, resp, ms):
    try:
        cost = litellm.completion_cost(completion_response=resp) or 0.0
    except Exception:
        cost = 0.0
    u = resp.usage
    usage.log(model, u.prompt_tokens, u.completion_tokens, cost, ms)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    t = time.time()
    model, r = _call(req.question)
    ms = int((time.time() - t) * 1000)
    _record(model, r, ms)
    answer, grounded = _parse(r.choices[0].message.content or "")
    return ChatResponse(answer=answer, grounded=grounded, model=model, latency_ms=ms)


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    t = time.time()
    model, stream = _call(req.question, stream=True)

    def gen():
        chunks = []
        for ch in stream:
            chunks.append(ch)
            tok = ch.choices[0].delta.content if ch.choices else None
            if tok:
                yield f"data: {json.dumps({'token': tok})}\n\n"
        ms = int((time.time() - t) * 1000)
        try:
            full = litellm.stream_chunk_builder(chunks, messages=_messages(req.question))
            _record(model, full, ms)
        except Exception as e:
            print("stream usage failed:", e)
        yield f"data: {json.dumps({'done': True, 'model': model, 'latency_ms': ms})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")