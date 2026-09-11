"""Compact serialization of canvas state for model context."""
from __future__ import annotations
import json
from canvas import Element

def serialize_canvas(canvas: list[Element]) -> str:
    if not canvas:
        return "The canvas is empty."
    summary = [
        {
            "id": element.get("id"),
            "type": element.get("type"),
            "label": element.get("text", ""),
            "x": element.get("x"),
            "y": element.get("y"),
            "width": element.get("width"),
            "height": element.get("height"),
            "backgroundColor": element.get("backgroundColor"),
        }
        for element in canvas
    ]
    return json.dumps(summary, indent=2)
