"""OpenAI tool schemas and canvas-bound tool implementations."""

from __future__ import annotations

from typing import Any, Callable

from canvas import Element, replace_canvas, update_element


ELEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique element identifier."},
        "type": {
            "type": "string",
            "enum": ["rectangle", "ellipse", "diamond", "text", "arrow", "line"],
        },
        "x": {"type": "number"},
        "y": {"type": "number"},
        "width": {"type": "number"},
        "height": {"type": "number"},
        "text": {"type": "string", "description": "Optional visible label."},
        "strokeColor": {"type": "string"},
        "backgroundColor": {"type": "string"},
        "fontSize": {"type": "number"},
    },
    "required": ["id", "type", "x", "y", "width", "height"],
    "additionalProperties": False,
}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_diagram",
            "description": (
                "Create a complete new diagram. Use this when the user asks "
                "to draw, create, or design a diagram from scratch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "array",
                        "items": ELEMENT_SCHEMA,
                    }
                },
                "required": ["elements"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_diagram",
            "description": (
                "Modify one existing diagram element by its exact id. "
                "Only include fields that should change."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "element_id": {"type": "string"},
                    "updates": {"type": "object"},
                },
                "required": ["element_id", "updates"],
                "additionalProperties": False,
            },
        },
    },
]


ToolFunction = Callable[[dict[str, Any]], str]


def make_tool_functions(canvas: list[Element]) -> dict[str, ToolFunction]:

    def generate(args: dict[str, Any]) -> str:
        return replace_canvas(canvas, args["elements"])

    def modify(args: dict[str, Any]) -> str:
        return update_element(canvas, args["element_id"], args["updates"])

    return {
        "generate_diagram": generate,
        "modify_diagram": modify,
    }
