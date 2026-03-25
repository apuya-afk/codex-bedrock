import json
import time
import uuid
from typing import AsyncIterable

from fastapi import APIRouter, Body, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from codex_bedrock.auth import require_api_key
from codex_bedrock.models.bedrock import BedrockModel
from codex_bedrock.schema import (
    AssistantMessage,
    ChatRequest,
    Function,
    ResponseFunction,
    SystemMessage,
    Tool,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from codex_bedrock.config import DEFAULT_MODEL, MODEL_MAP

router = APIRouter(prefix="")


def _translate_input(input_data, instructions=None) -> list:
    """Translate Responses API input → Chat Completions messages."""
    messages = []

    if instructions:
        messages.append(SystemMessage(role="system", content=instructions))

    if isinstance(input_data, str):
        messages.append(UserMessage(role="user", content=input_data))
        return messages

    for item in input_data:
        if isinstance(item, str):
            messages.append(UserMessage(role="user", content=item or " "))
            continue

        item_type = item.get("type", "")
        role = item.get("role", "")

        # Stateful function_call item (assistant tool use)
        if item_type == "function_call":
            tc = ToolCall(
                id=item.get("id") or item.get("call_id") or f"call_{uuid.uuid4().hex[:8]}",
                type="function",
                function=ResponseFunction(
                    name=item.get("name", ""),
                    arguments=item.get("arguments", "{}"),
                ),
            )
            messages.append(AssistantMessage(role="assistant", content=None, tool_calls=[tc]))
            continue

        # Stateful function_call_output item (tool result)
        if item_type == "function_call_output":
            output = item.get("output", "")
            if not isinstance(output, str):
                output = json.dumps(output)
            messages.append(ToolMessage(
                role="tool",
                content=output,
                tool_call_id=item.get("call_id") or item.get("id") or "",
            ))
            continue

        content = item.get("content", "")

        if role == "system":
            text = _extract_text(content, input_types=("input_text", "text"))
            messages.append(SystemMessage(role="system", content=text))

        elif role == "user":
            text = _extract_text(content, input_types=("input_text", "text"))
            messages.append(UserMessage(role="user", content=text))

        elif role == "assistant":
            text = None
            tool_calls = None
            if isinstance(content, list):
                text_parts = []
                tool_calls = []
                for c in content:
                    ctype = c.get("type", "")
                    if ctype in ("output_text", "text"):
                        text_parts.append(c.get("text", ""))
                    elif ctype == "tool_use":
                        args = c.get("input", {})
                        tool_calls.append(ToolCall(
                            id=c.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                            type="function",
                            function=ResponseFunction(
                                name=c.get("name", ""),
                                arguments=json.dumps(args) if isinstance(args, dict) else args,
                            ),
                        ))
                text = " ".join(text_parts) if text_parts else None
                tool_calls = tool_calls if tool_calls else None
            else:
                text = content or None
            messages.append(AssistantMessage(role="assistant", content=text, tool_calls=tool_calls))

    # Bedrock requires conversation to start with a user message
    non_system = [m for m in messages if not isinstance(m, SystemMessage)]
    if not non_system or not isinstance(non_system[0], UserMessage):
        first_system_idx = next((i for i, m in enumerate(messages) if isinstance(m, SystemMessage)), -1)
        messages.insert(first_system_idx + 1, UserMessage(role="user", content=" "))

    return messages


def _extract_text(content, input_types=("text",)) -> str:
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if c.get("type") in input_types)
    return content or ""


def _sanitize_schema(schema: dict) -> dict:
    """Ensure tool schema is valid for Bedrock (type must be 'object')."""
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}
    schema = dict(schema)
    if schema.get("type") != "object":
        schema["type"] = "object"
    if "properties" not in schema:
        schema["properties"] = {}
    return schema


def _translate_tools(tools_data) -> list[Tool] | None:
    if not tools_data:
        return None
    result = []
    for t in tools_data:
        func = t.get("function", t)
        if t.get("type") == "function" or "name" in func:
            result.append(Tool(
                type="function",
                function=Function(
                    name=func.get("name", ""),
                    description=func.get("description"),
                    parameters=_sanitize_schema(func.get("parameters", {})),
                ),
            ))
    return result or None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _stream_responses(
    chat_request: ChatRequest,
    response_id: str,
    msg_id: str,
    model_name: str,
) -> AsyncIterable[str]:
    model = BedrockModel()
    model.validate(chat_request)

    created_at = int(time.time())

    yield _sse("response.created", {
        "type": "response.created",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": "in_progress",
            "model": model_name,
            "output": [],
        },
    })

    # Tracking state
    next_output_index = 0
    full_text = ""
    text_output_index = None
    content_index = 0
    text_part_started = False

    tool_calls: dict[int, dict] = {}  # stream delta index -> accumulated info

    async for chunk_bytes in model.chat_stream(chat_request):
        chunk_str = chunk_bytes.decode("utf-8").strip()
        if chunk_str.startswith("data: "):
            chunk_str = chunk_str[6:]
        if not chunk_str or chunk_str == "[DONE]":
            continue

        try:
            chunk = json.loads(chunk_str)
        except Exception:
            continue

        choices = chunk.get("choices", [])
        if not choices:
            continue

        delta = choices[0].get("delta", {})

        # --- Text content ---
        text_delta = delta.get("content")
        if text_delta:
            if text_output_index is None:
                text_output_index = next_output_index
                next_output_index += 1
                yield _sse("response.output_item.added", {
                    "type": "response.output_item.added",
                    "output_index": text_output_index,
                    "item": {
                        "type": "message",
                        "id": msg_id,
                        "status": "in_progress",
                        "role": "assistant",
                        "content": [],
                    },
                })
                yield _sse("response.content_part.added", {
                    "type": "response.content_part.added",
                    "item_id": msg_id,
                    "output_index": text_output_index,
                    "content_index": content_index,
                    "part": {"type": "output_text", "text": ""},
                })
                text_part_started = True

            full_text += text_delta
            yield _sse("response.output_text.delta", {
                "type": "response.output_text.delta",
                "item_id": msg_id,
                "output_index": text_output_index,
                "content_index": content_index,
                "delta": text_delta,
            })

        # --- Tool calls ---
        for tc_delta in delta.get("tool_calls") or []:
            tc_idx = tc_delta.get("index", 0)

            if tc_idx not in tool_calls:
                call_id = tc_delta.get("id") or f"call_{uuid.uuid4().hex[:8]}"
                out_idx = next_output_index
                next_output_index += 1
                tool_calls[tc_idx] = {
                    "id": call_id,
                    "name": "",
                    "arguments": "",
                    "output_index": out_idx,
                }
                yield _sse("response.output_item.added", {
                    "type": "response.output_item.added",
                    "output_index": out_idx,
                    "item": {
                        "type": "function_call",
                        "id": call_id,
                        "call_id": call_id,
                        "name": "",
                        "arguments": "",
                    },
                })

            func = tc_delta.get("function", {})
            if func.get("name"):
                tool_calls[tc_idx]["name"] += func["name"]
            if func.get("arguments"):
                tool_calls[tc_idx]["arguments"] += func["arguments"]
                yield _sse("response.function_call_arguments.delta", {
                    "type": "response.function_call_arguments.delta",
                    "item_id": tool_calls[tc_idx]["id"],
                    "output_index": tool_calls[tc_idx]["output_index"],
                    "delta": func["arguments"],
                })

    # --- Finalize text ---
    if text_part_started and text_output_index is not None:
        yield _sse("response.output_text.done", {
            "type": "response.output_text.done",
            "item_id": msg_id,
            "output_index": text_output_index,
            "content_index": content_index,
            "text": full_text,
        })
        yield _sse("response.content_part.done", {
            "type": "response.content_part.done",
            "item_id": msg_id,
            "output_index": text_output_index,
            "content_index": content_index,
            "part": {"type": "output_text", "text": full_text},
        })
        yield _sse("response.output_item.done", {
            "type": "response.output_item.done",
            "output_index": text_output_index,
            "item": {
                "type": "message",
                "id": msg_id,
                "status": "completed",
                "role": "assistant",
                "content": [{"type": "output_text", "text": full_text}],
            },
        })

    # --- Finalize tool calls ---
    for tc in tool_calls.values():
        yield _sse("response.function_call_arguments.done", {
            "type": "response.function_call_arguments.done",
            "item_id": tc["id"],
            "output_index": tc["output_index"],
            "arguments": tc["arguments"],
        })
        yield _sse("response.output_item.done", {
            "type": "response.output_item.done",
            "output_index": tc["output_index"],
            "item": {
                "type": "function_call",
                "id": tc["id"],
                "call_id": tc["id"],
                "name": tc["name"],
                "arguments": tc["arguments"],
                "status": "completed",
            },
        })

    # --- Build final output list ---
    output_items = {}
    if text_output_index is not None:
        output_items[text_output_index] = {
            "type": "message",
            "id": msg_id,
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": full_text}],
        }
    for tc in tool_calls.values():
        output_items[tc["output_index"]] = {
            "type": "function_call",
            "id": tc["id"],
            "call_id": tc["id"],
            "name": tc["name"],
            "arguments": tc["arguments"],
            "status": "completed",
        }
    output_list = [output_items[i] for i in sorted(output_items)]

    yield _sse("response.completed", {
        "type": "response.completed",
        "response": {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": "completed",
            "model": model_name,
            "output": output_list,
        },
    })

    yield "data: [DONE]\n\n"


def _build_chat_request(request: dict) -> tuple[ChatRequest, str, str, str]:
    response_id = f"resp_{uuid.uuid4().hex}"
    msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    model_name = MODEL_MAP.get(request.get("model", DEFAULT_MODEL), DEFAULT_MODEL)
    chat_request = ChatRequest(
        model=model_name,
        messages=_translate_input(request.get("input", []), request.get("instructions")),
        stream=bool(request.get("stream", False)),
        tools=_translate_tools(request.get("tools")),
        temperature=request.get("temperature"),
        top_p=request.get("top_p"),
        max_tokens=request.get("max_output_tokens") or 4096,
    )
    return chat_request, response_id, msg_id, model_name


@router.websocket("/responses")
async def responses_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        request = await websocket.receive_json()
        chat_request, response_id, msg_id, model_name = _build_chat_request({**request, "stream": True})

        async for event_str in _stream_responses(chat_request, response_id, msg_id, model_name):
            # Strip SSE framing ("event: X\ndata: Y\n\n") — send raw JSON over WebSocket
            for line in event_str.strip().splitlines():
                if line.startswith("data: ") and line[6:] != "[DONE]":
                    await websocket.send_text(line[6:])

        await websocket.close()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
            await websocket.close()
        except Exception:
            pass


@router.post("/responses", dependencies=[Depends(require_api_key)])
async def create_response(request: dict = Body(...)):
    chat_request, response_id, msg_id, model_name = _build_chat_request(request)
    stream = request.get("stream", False)

    if stream:
        return StreamingResponse(
            content=_stream_responses(chat_request, response_id, msg_id, model_name),
            media_type="text/event-stream",
        )

    # Non-streaming
    model = BedrockModel()
    model.validate(chat_request)
    result = await model.chat(chat_request)

    content = ""
    tool_calls_out = []
    if hasattr(result, "choices") and result.choices:
        msg = result.choices[0].message
        content = msg.content or ""
        for tc in msg.tool_calls or []:
            tool_calls_out.append({
                "type": "function_call",
                "id": tc.id,
                "call_id": tc.id,
                "name": tc.function.name,
                "arguments": tc.function.arguments,
                "status": "completed",
            })

    output = []
    if content:
        output.append({
            "type": "message",
            "id": msg_id,
            "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": content}],
        })
    output.extend(tool_calls_out)

    usage = {}
    if hasattr(result, "usage") and result.usage:
        usage = {
            "input_tokens": result.usage.prompt_tokens,
            "output_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
        }

    return {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": model_name,
        "output": output,
        "usage": usage,
    }
