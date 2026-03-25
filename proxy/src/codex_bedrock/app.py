import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from codex_bedrock.config import ALLOWED_ORIGINS
from codex_bedrock.routers import chat, models, responses

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="codex-bedrock",
    description="OpenAI-compatible proxy for AWS Bedrock — powers Codex CLI",
    version="0.1.0",
)

origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS != "*" else ["*"]
if origins != ["*"]:
    logging.info("CORS restricted to: %s", origins)
else:
    logging.warning("CORS allows all origins — set ALLOWED_ORIGINS env var to restrict")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # nosec
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/v1"
app.include_router(models.router, prefix=PREFIX)
app.include_router(chat.router, prefix=PREFIX)
app.include_router(responses.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    logging.warning("Validation error: %s %s — %s", request.method, request.url.path, str(exc).split("\n")[0])
    return PlainTextResponse(str(exc), status_code=400)
