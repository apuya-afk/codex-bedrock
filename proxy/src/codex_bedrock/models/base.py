import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable

from codex_bedrock.schema import (
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
    Error,
)


class BaseChatModel(ABC):
    def validate(self, chat_request: ChatRequest) -> None:
        pass

    @abstractmethod
    async def chat(self, chat_request: ChatRequest) -> ChatResponse:
        pass

    @abstractmethod
    async def chat_stream(self, chat_request: ChatRequest) -> AsyncIterable[bytes]:
        pass

    @staticmethod
    def generate_message_id() -> str:
        return "chatcmpl-" + str(uuid.uuid4())[:8]

    @staticmethod
    def stream_response_to_bytes(response: ChatStreamResponse | Error | None = None) -> bytes:

        if isinstance(response, Error):
            data = response.model_dump_json()
        elif isinstance(response, ChatStreamResponse):
            response.system_fingerprint = "fp"
            response.object = "chat.completion.chunk"
            response.created = int(time.time())
            data = response.model_dump_json(exclude_unset=True)
        else:
            data = "[DONE]"
        return f"data: {data}\n\n".encode()


class BaseEmbeddingsModel(ABC):
    @abstractmethod
    def embed(self, embeddings_request):
        pass
