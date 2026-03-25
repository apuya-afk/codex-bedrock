from fastapi import APIRouter, Depends

from codex_bedrock.auth import require_api_key
from codex_bedrock.models.bedrock import BedrockModel
from codex_bedrock.schema import Models

router = APIRouter(prefix="/models", dependencies=[Depends(require_api_key)])


@router.get("", response_model=Models)
@router.get("/", response_model=Models)
async def list_models() -> Models:
    model = BedrockModel()
    return Models(data=model.list_models())
