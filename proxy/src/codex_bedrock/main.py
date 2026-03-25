import uvicorn

from codex_bedrock.config import HOST, PORT


def main():
    uvicorn.run(
        "codex_bedrock.app:app",
        host=HOST,
        port=PORT,
        ws="websockets",
        log_level="info",
    )


if __name__ == "__main__":
    main()
