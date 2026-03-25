import os

API_KEY = os.environ.get("CODEX_BEDROCK_API_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "51822"))
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "null")

# Default model used when none is specified in the request
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "us.anthropic.claude-sonnet-4-6")

# Maps Codex built-in model IDs → Bedrock model IDs.
# Users can override individual entries via env vars:
#   CODEX_BEDROCK_MODEL_FLAGSHIP, CODEX_BEDROCK_MODEL_BALANCED, CODEX_BEDROCK_MODEL_FAST
MODEL_MAP: dict[str, str] = {
    "gpt-5.4": os.environ.get("CODEX_BEDROCK_MODEL_FLAGSHIP", "us.anthropic.claude-opus-4-6-v1"),
    "gpt-5.2": os.environ.get("CODEX_BEDROCK_MODEL_BALANCED", "us.anthropic.claude-sonnet-4-6"),
    "gpt-5.1": os.environ.get("CODEX_BEDROCK_MODEL_FAST", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
}

ENABLE_CROSS_REGION_INFERENCE = os.environ.get("ENABLE_CROSS_REGION_INFERENCE", "true").lower() == "true"
ENABLE_APPLICATION_INFERENCE_PROFILES = os.environ.get("ENABLE_APPLICATION_INFERENCE_PROFILES", "true").lower() == "true"
ENABLE_PROMPT_CACHING = os.environ.get("ENABLE_PROMPT_CACHING", "false").lower() == "true"
