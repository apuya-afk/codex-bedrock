import time
from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, Field

from codex_bedrock.config import DEFAULT_MODEL


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageUrl(BaseModel):
    url: str
    detail: str | None = "auto"


class ImageContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: ImageUrl


class ToolContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ResponseFunction(BaseModel):
    name: str | None = None
    arguments: str


class ToolCall(BaseModel):
    index: int | None = None
    id: str | None = None
    type: Literal["function"] = "function"
    function: ResponseFunction


class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str
    name: str | None = None


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str | list[TextContent | ImageContent]
    name: str | None = None


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    name: str | None = None


class ToolMessage(BaseModel):
    role: Literal["tool"] = "tool"
    content: str | list[ToolContent] | list[dict]
    tool_call_id: str


class DeveloperMessage(BaseModel):
    role: Literal["developer"] = "developer"
    content: str
    name: str | None = None


class Function(BaseModel):
    name: str
    description: str | None = None
    parameters: object


class Tool(BaseModel):
    type: Literal["function"] = "function"
    function: Function


class StreamOptions(BaseModel):
    include_usage: bool = True


class ChatRequest(BaseModel):
    messages: list[SystemMessage | UserMessage | AssistantMessage | ToolMessage | DeveloperMessage]
    model: str = DEFAULT_MODEL
    stream: bool | None = False
    stream_options: StreamOptions | None = None
    temperature: float | None = Field(default=None, le=2.0, ge=0.0)
    top_p: float | None = Field(default=None, le=1.0, ge=0.0)
    max_tokens: int | None = 4096
    max_completion_tokens: int | None = None
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    tools: list[Tool] | None = None
    tool_choice: str | object = "auto"
    stop: list[str] | str | None = None
    frequency_penalty: float | None = Field(default=0.0, le=2.0, ge=-2.0)
    presence_penalty: float | None = Field(default=0.0, le=2.0, ge=-2.0)
    n: int | None = 1
    user: str | None = None
    extra_body: dict | None = None


class ChatResponseMessage(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    reasoning_content: str | None = None


class Choice(BaseModel):
    index: int | None = 0
    message: ChatResponseMessage
    finish_reason: str | None = None
    logprobs: dict | None = None


class ChoiceDelta(BaseModel):
    index: int | None = 0
    delta: ChatResponseMessage
    finish_reason: str | None = None
    logprobs: dict | None = None


class PromptTokensDetails(BaseModel):
    cached_tokens: int = 0
    audio_tokens: int = 0


class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int = 0
    audio_tokens: int = 0


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: PromptTokensDetails | None = None
    completion_tokens_details: CompletionTokensDetails | None = None


class BaseChatResponse(BaseModel):
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    system_fingerprint: str = "fp"


class ChatResponse(BaseChatResponse):
    object: Literal["chat.completion"] = "chat.completion"
    choices: list[Choice]
    usage: Usage


class ChatStreamResponse(BaseChatResponse):
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    choices: list[ChoiceDelta]
    usage: Usage | None = None


class Model(BaseModel):
    id: str
    created: int = Field(default_factory=lambda: int(time.time()))
    object: str | None = "model"
    owned_by: str | None = "bedrock"


class Models(BaseModel):
    object: str | None = "list"
    data: list[Model] = []


class EmbeddingsRequest(BaseModel):
    input: str | list[str] | Iterable[int | Iterable[int]]
    model: str
    encoding_format: Literal["float", "base64"] = "float"
    dimensions: int | None = None
    user: str | None = None


class Embedding(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: list[float] | bytes
    index: int


class EmbeddingsUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[Embedding]
    model: str
    usage: EmbeddingsUsage


class ErrorMessage(BaseModel):
    message: str


class Error(BaseModel):
    error: ErrorMessage
