"""OpenAI-compatible model client and bounded tool-calling loop."""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from canvas import Element
from tools import TOOLS, make_tool_functions
from context import serialize_canvas

load_dotenv()

MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")
MAX_STEPS = 10


def build_client() -> OpenAI:
    api_key = os.getenv("AVALAI_API_KEY")
    if not api_key:
        raise RuntimeError("API_KEY is not set. Add it to your .env file.")
    return OpenAI(
        api_key=api_key,
        base_url=os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1"),
    )


SYSTEM_PROMPT = """You are a diagram design assistant controlling a canvas.
Use generate_diagram to create a complete diagram from scratch.
Use modify_diagram to change one existing element when the user requests a modification.
Give every element a unique id and use valid element types.
Do not merely turn every noun in the prompt into a rectangle.
First infer each component's role and the meaningful relationships between components.
Use diamonds for decisions, ellipses for start/end states when appropriate, and rectangles
for processes, services, or systems. Add arrows only for real directional relationships.
Group or layer components when the architecture implies clients, services, dependencies,
or data stores. Lay flows out left-to-right or top-to-bottom with readable spacing.
After tool work, briefly summarize what changed.
"""


def run_turn(
        messages: list[dict[str, Any]],
        canvas: list[Element],
        client: OpenAI | None = None,
        tools: list[dict[str, Any]] = TOOLS,
) -> str:
    client = client or build_client()
    tool_functions = make_tool_functions(canvas)

    for _ in range(MAX_STEPS):
        contextual_messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "system",
                "content": (
                        "Current canvas state:\n"
                        + serialize_canvas(canvas)
                ),
            },
            *messages,
        ]

        response = client.chat.completions.create(
            model=MODEL,
            messages=contextual_messages,
            tools=tools,
        )
        message = response.choices[0].message
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
        }

        if message.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in message.tool_calls
            ]
        messages.append(assistant_message)

        if not message.tool_calls:
            return message.content or ""

        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments)
                function = tool_functions.get(call.function.name)
                if function is None:
                    result = f"Error: unknown tool {call.function.name!r}."
                else:
                    result = function(arguments)
            except Exception as error:
                result = f"Error while running {call.function.name}: {error}"

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })

    return "Stopped: reached the maximum number of agent steps."


def run_turn_streaming(messages, canvas, client=None, tools=TOOLS):
    client = client or build_client()
    tool_functions = make_tool_functions(canvas)
    for _ in range(MAX_STEPS):
        stream = client.chat.completions.create(model=MODEL, messages=messages, tools=tools, stream=True)
        parts, calls = [], {}
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end='', flush=True);
                parts.append(delta.content)
            for part in delta.tool_calls or []:
                call = calls.setdefault(part.index, {'id': '', 'name': '', 'arguments': ''})
                if part.id: call['id'] = part.id
                if part.function and part.function.name:
                    call['name'] = part.function.name;
                    print(f"\n⚙ {call['name']} …", flush=True)
                if part.function and part.function.arguments: call['arguments'] += part.function.arguments
        assistant = {'role': 'assistant', 'content': ''.join(parts)}
        if calls: assistant['tool_calls'] = [
            {'id': c['id'], 'type': 'function', 'function': {'name': c['name'], 'arguments': c['arguments']}} for c in
            calls.values()]
        messages.append(assistant)
        if not calls: print(); return assistant['content']
        for call in assistant['tool_calls']:
            try:
                fn = tool_functions.get(call['function']['name'])
                result = fn(json.loads(call['function']['arguments'])) if fn else 'Error: unknown tool.'
            except Exception as error:
                result = f'Error while running tool: {error}'
            messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': result})
    return 'Stopped: reached the maximum number of agent steps.'
