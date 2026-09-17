"""OpenAI tool schemas and canvas-bound tool implementations."""

from __future__ import annotations

from typing import Any, Callable

from canvas import Element, connect_elements, replace_canvas, update_element


ELEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "Unique element identifier."},
        "type": {
            "type": "string",
            "enum": ["rectangle", "ellipse", "diamond", "text"],
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
                "Create the nodes for a new diagram. Do not create arrows here. "
                "After the nodes exist, use connect_elements with their exact IDs."
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
            "name": "connect_elements",
            "description": (
                "Add directed relationships between existing nodes. Coordinates are "
                "calculated automatically. Use semantic source and target IDs from "
                "the current canvas, and include a short relationship label."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "connections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "source_id": {"type": "string"},
                                "target_id": {"type": "string"},
                                "label": {"type": "string"},
                                "strokeColor": {"type": "string"}
                            },
                            "required": ["source_id", "target_id", "label"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["connections"],
                "additionalProperties": False
            }
        }
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

    def connect(args: dict[str, Any]) -> str:
        return connect_elements(canvas, args["connections"])

    return {
        "generate_diagram": generate,
        "connect_elements": connect,
        "modify_diagram": modify,
    }
