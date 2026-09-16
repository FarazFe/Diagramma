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

PLAN_PROMPT = """Create a concise design plan for the requested diagram. Do not call tools.
Infer semantics instead of copying nouns into a row of boxes.

Return these four sections:
- Purpose: what the diagram communicates and the appropriate diagram type.
- Components: each component's role and an appropriate shape.
- Relationships: meaningful directed connections, including short arrow labels.
- Layout: layers or groups and approximate positions that avoid overlaps.

For architecture diagrams, distinguish clients, internal services, external providers,
and data stores. Do not assume every component connects to the next component in the
order it appears in the prompt.
"""


def create_plan(client: OpenAI, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLAN_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or "No plan returned."


def messages_with_context(
        messages: list[dict[str, Any]], canvas: list[Element]
) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": "Current canvas state:\n" + serialize_canvas(canvas)},
        *[message for message in messages if message.get("role") != "system"],
    ]


def add_creation_plan(
        messages: list[dict[str, Any]], canvas: list[Element], client: OpenAI
) -> str | None:
    if canvas:
        return None
    user_prompt = next(
        (message["content"] for message in reversed(messages) if message.get("role") == "user"),
        None,
    )
    if not user_prompt:
        return None
    plan = create_plan(client, user_prompt)
    messages.append({"role": "assistant", "content": f"Diagram plan:\n{plan}"})
    return plan


def run_turn(
        messages: list[dict[str, Any]],
        canvas: list[Element],
        client: OpenAI | None = None,
        tools: list[dict[str, Any]] = TOOLS,
) -> str:
    client = client or build_client()
    tool_functions = make_tool_functions(canvas)
    add_creation_plan(messages, canvas, client)

    for _ in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages_with_context(messages, canvas),
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
    plan = add_creation_plan(messages, canvas, client)
    if plan:
        print(f"Planning diagram…\n{plan}\n", flush=True)
    for _ in range(MAX_STEPS):
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages_with_context(messages, canvas),
            tools=tools,
            stream=True,
        )
        parts, calls = [], {}
        for chunk in stream:
            if not chunk.choices:
                continue
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
