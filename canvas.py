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
    sourceId: str
    targetId: str


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


def _center(element: Element) -> tuple[float, float]:
    return (
        element["x"] + element.get("width", 0) / 2,
        element["y"] + element.get("height", 0) / 2,
    )


def _edge_point(element: Element, toward: Element) -> tuple[float, float]:
    center_x, center_y = _center(element)
    target_x, target_y = _center(toward)
    delta_x = target_x - center_x
    delta_y = target_y - center_y
    half_width = max(element.get("width", 0) / 2, 1)
    half_height = max(element.get("height", 0) / 2, 1)
    scale = 1 / max(abs(delta_x) / half_width, abs(delta_y) / half_height, 1e-9)
    return center_x + delta_x * scale, center_y + delta_y * scale


def connect_elements(canvas: list[Element], connections: list[dict[str, Any]]) -> str:
    """Add directed arrows between existing elements using their IDs."""
    elements_by_id = {
        element["id"]: element
        for element in canvas
        if element.get("type") not in {"arrow", "line"}
    }
    existing_ids = {element["id"] for element in canvas}
    new_arrows: list[Element] = []

    for index, connection in enumerate(connections, start=1):
        source_id = connection["source_id"]
        target_id = connection["target_id"]
        source = elements_by_id.get(source_id)
        target = elements_by_id.get(target_id)
        if source is None or target is None:
            return f"Error: cannot connect {source_id!r} to {target_id!r}; element not found."

        arrow_id = connection.get("id") or f"arrow_{source_id}_to_{target_id}"
        if arrow_id in existing_ids:
            arrow_id = f"{arrow_id}_{index}"
        start_x, start_y = _edge_point(source, target)
        end_x, end_y = _edge_point(target, source)
        arrow: Element = {
            "id": arrow_id,
            "type": "arrow",
            "x": start_x,
            "y": start_y,
            "width": end_x - start_x,
            "height": end_y - start_y,
            "sourceId": source_id,
            "targetId": target_id,
        }
        if connection.get("label"):
            arrow["text"] = connection["label"]
        if connection.get("strokeColor"):
            arrow["strokeColor"] = connection["strokeColor"]
        new_arrows.append(arrow)
        existing_ids.add(arrow_id)

    canvas.extend(new_arrows)
    return f"Connected {len(new_arrows)} relationships."
