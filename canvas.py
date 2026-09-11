"""The in-memory diagram canvas and its mutation operations."""

from __future__ import annotations

from typing import Any, TypedDict


ELEMENT_TYPES = {"rectangle", "ellipse", "diamond", "text", "arrow", "line"}


class Element(TypedDict, total=False):
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    text: str
    strokeColor: str
    backgroundColor: str
    fontSize: float


def validate_element(element: dict[str, Any]) -> str | None:
    """Return an error message, or None when an element is valid."""
    required = ("id", "type", "x", "y", "width", "height")
    missing = [field for field in required if field not in element]
    if missing:
        return f"Missing required fields: {', '.join(missing)}."
    if not isinstance(element["id"], str) or not element["id"].strip():
        return "Element id must be a non-empty string."
    if element["type"] not in ELEMENT_TYPES:
        return f"Unknown element type: {element['type']!r}."
    for field in ("x", "y", "width", "height"):
        if not isinstance(element[field], (int, float)):
            return f"Element field {field!r} must be numeric."
    return None


def replace_canvas(canvas: list[Element], elements: list[dict[str, Any]]) -> str:
    """Replace the canvas after validating every incoming element."""
    seen_ids: set[str] = set()
    for element in elements:
        error = validate_element(element)
        if error:
            return f"Error: {error}"
        if element["id"] in seen_ids:
            return f"Error: duplicate element id {element['id']!r}."
        seen_ids.add(element["id"])

    canvas[:] = [dict(element) for element in elements]
    return f"Canvas replaced: {len(elements)} elements."


def update_element(
    canvas: list[Element], element_id: str, updates: dict[str, Any]
) -> str:
    """Apply only requested fields to one existing element."""
    for element in canvas:
        if element["id"] != element_id:
            continue
        candidate = {**element, **updates}
        error = validate_element(candidate)
        if error:
            return f"Error: {error}"
        element.update({key: value for key, value in updates.items() if value is not None})
        return f"Updated {element_id}."
    return f"No element with id {element_id!r} on the canvas."

