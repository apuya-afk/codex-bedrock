# codex-bedrock

> Use [Codex CLI](https://github.com/openai/codex) with AWS Bedrock + SSO — zero OpenAI account required.

[![CI](https://github.com/apuya-afk/codex-bedrock/actions/workflows/ci.yml/badge.svg)](https://github.com/apuya-afk/codex-bedrock/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/codex-bedrock)](https://www.npmjs.com/package/codex-bedrock)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Codex CLI is built for OpenAI's API. `codex-bedrock` is a local proxy that translates Codex's requests into AWS Bedrock API calls, so you can use Claude models via your existing AWS account and SSO credentials — no OpenAI subscription needed.

## How it works

```
codex CLI  →  codex-bedrock proxy (localhost)  →  AWS Bedrock  →  Claude
```

The proxy implements OpenAI's [Responses API](https://platform.openai.com/docs/api-reference/responses) and WebSocket transport, which is what Codex uses internally. It runs entirely on your machine — no traffic goes through any third-party service.

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) — `brew install codex` or `npm install -g @openai/codex`
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) with an SSO profile configured
- Python 3.11+
- AWS account with Bedrock access and Claude models enabled in your region

## Setup

```bash
npx codex-bedrock setup
```

That's it. The setup command will:
1. Check prerequisites
2. Ask for your AWS profile and region
3. Validate your SSO session (and log you in if expired)
4. Install the proxy
5. Patch `~/.codex/config.toml` to point at the local proxy
6. Add a `codex()` shell function to your RC file that auto-starts the proxy

After setup, just run:

```bash
source ~/.zshrc  # or restart your terminal
codex
```

## Model mapping

Codex's built-in model picker maps to Claude models on Bedrock:

| Codex model | Claude model | Tier |
|---|---|---|
| `gpt-5.4` | Claude Opus 4.6 | Flagship |
| `gpt-5.2` | Claude Sonnet 4.6 | Balanced |
| `gpt-5.1` | Claude Haiku 4.5 | Fast |

You can override any mapping with environment variables:

```bash
export CODEX_BEDROCK_MODEL_FLAGSHIP=us.anthropic.claude-opus-4-6-v1
export CODEX_BEDROCK_MODEL_BALANCED=us.anthropic.claude-sonnet-4-6
export CODEX_BEDROCK_MODEL_FAST=us.anthropic.claude-haiku-4-5-20251001-v1:0
```

## Commands

```bash
codex-bedrock setup   # One-time interactive setup
codex-bedrock start   # Start the proxy (done automatically by the codex() shell function)
codex-bedrock stop    # Stop the proxy
codex-bedrock status  # Show proxy status and model mapping
```

## Manual proxy start

If you prefer to manage the proxy yourself:

```bash
codex-bedrock start --profile my-aws-profile --region us-east-1
```

## AWS SSO token refresh

SSO tokens typically expire after 8 hours. The `codex()` shell function automatically checks and refreshes the token when you start a session. You can also run `aws sso login --profile <profile>` manually.

## Security

- The proxy binds to `127.0.0.1` only — not reachable from outside your machine
- CORS is restricted to `null` origin by default (blocks browser tabs from calling it)
- AWS credentials are never stored — only the SSO session token managed by the AWS CLI is used
- The local API key is randomly generated during setup and stored in `~/.codex-bedrock/config.json`

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

```bash
git clone https://github.com/apuya-afk/codex-bedrock
cd codex-bedrock
npm install
npm run dev        # Watch TypeScript
```

## License

MIT — see [LICENSE](LICENSE).

Portions of the proxy are derived from [aws-samples/bedrock-access-gateway](https://github.com/aws-samples/bedrock-access-gateway), Apache License 2.0. See [NOTICE](NOTICE).
