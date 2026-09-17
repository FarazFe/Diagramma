"""Export the canonical canvas model as an Excalidraw scene file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from canvas import Element


def _base_element(element: Element, index: int) -> dict[str, Any]:
    return {
        "id": element["id"], "type": element["type"], "x": element["x"],
        "y": element["y"], "width": element.get("width", 0),
        "height": element.get("height", 0), "angle": 0,
        "strokeColor": element.get("strokeColor", "#1e1e1e"),
        "backgroundColor": element.get("backgroundColor", "transparent"),
        "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
        "index": f"a{index:06d}", "roundness": {"type": 3}, "seed": index + 1,
        "version": 1, "versionNonce": index + 1, "isDeleted": False,
        "boundElements": [], "updated": 1, "link": None, "locked": False,
        "customData": {"canvasId": element["id"]},
    }


def _text_element(element: Element, index: int) -> dict[str, Any]:
    text = str(element.get("text", ""))
    text_element = _base_element({**element, "id": f"{element['id']}_text", "type": "text"}, index)
    text_element.update({
        "text": text, "fontSize": element.get("fontSize", 16),
        "fontFamily": 1, "textAlign": "center", "verticalAlign": "middle",
        "containerId": element["id"], "originalText": text,
        "autoResize": True, "lineHeight": 1.25,
    })
    return text_element


def _shape_elements(canvas: list[Element]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    output = []
    shapes_by_id = {}
    for index, element in enumerate(canvas):
        if element.get("type") in {"arrow", "line"}:
            continue
        shape = _base_element(element, index * 2)
        shapes_by_id[element["id"]] = shape
        output.append(shape)
        if element.get("text"):
            text = _text_element(element, index * 2 + 1)
            shape["boundElements"].append({"type": "text", "id": text["id"]})
            output.append(text)
    return output, shapes_by_id


def _arrow_elements(canvas: list[Element], start_index: int, shapes_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for offset, element in enumerate(canvas):
        if element.get("type") != "arrow":
            continue
        arrow = _base_element(element, start_index + offset)
        source_id = element.get("sourceId")
        target_id = element.get("targetId")
        arrow.update({
            "points": [[0, 0], [element.get("width", 0), element.get("height", 0)]],
            "startBinding": ({"elementId": source_id, "focus": 0, "gap": 1, "fixedPoint": [0.5, 0.5]}
                             if source_id in shapes_by_id else None),
            "endBinding": ({"elementId": target_id, "focus": 0, "gap": 1, "fixedPoint": [0.5, 0.5]}
                           if target_id in shapes_by_id else None),
            "startArrowhead": None, "endArrowhead": "arrow",
        })
        for node_id in (source_id, target_id):
            if node_id in shapes_by_id:
                shapes_by_id[node_id]["boundElements"].append({"type": "arrow", "id": arrow["id"]})
        output.append(arrow)
    return output


def excalidraw_scene(canvas: list[Element]) -> dict[str, Any]:
    shapes, shapes_by_id = _shape_elements(canvas)
    return {
        "type": "excalidraw", "version": 2, "source": "diagram-agent",
        "elements": shapes + _arrow_elements(canvas, len(shapes), shapes_by_id),
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
        "files": {},
    }


def render_excalidraw(canvas: list[Element], path: str | Path = "canvas.excalidraw") -> Path:
    output_path = Path(path)
    output_path.write_text(json.dumps(excalidraw_scene(canvas), indent=2), encoding="utf-8")
    return output_path
