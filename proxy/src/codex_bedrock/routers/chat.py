from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from codex_bedrock.auth import require_api_key
from codex_bedrock.config import MODEL_MAP
from codex_bedrock.models.bedrock import BedrockModel
from codex_bedrock.schema import ChatRequest, ChatResponse, ChatStreamResponse, Error

router = APIRouter(prefix="/chat", dependencies=[Depends(require_api_key)])


@router.post("/completions", response_model=ChatResponse | ChatStreamResponse | Error, response_model_exclude_unset=True)
async def chat_completions(chat_request: ChatRequest):
    chat_request.model = MODEL_MAP.get(chat_request.model, chat_request.model)
    model = BedrockModel()
    model.validate(chat_request)
    if chat_request.stream:
        return StreamingResponse(content=model.chat_stream(chat_request), media_type="text/event-stream")
    return await model.chat(chat_request)
