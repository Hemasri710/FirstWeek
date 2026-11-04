"""Request and response models."""

from typing import Literal

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    name: str
    email: str


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    model: str | None = None


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)


class Citation(BaseModel):
    file: str
    start_line: int
    end_line: int


class ChatAnswer(BaseModel):
    answer: str
    citations: list[Citation] = []
    grounded: bool
    model: str
    latency_ms: int
