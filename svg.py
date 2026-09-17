"""Pure SVG rendering for the in-memory diagram canvas."""

from __future__ import annotations

import html
from pathlib import Path

from canvas import Element


def svg_string(canvas: list[Element]) -> str:
    parts: list[str] = []

    for element in canvas:
        element_type = element["type"]
        x = element["x"]
        y = element["y"]
        width = element.get("width", 0)
        height = element.get("height", 0)
        stroke = element.get("strokeColor", "#1e1e1e")
        fill = element.get("backgroundColor", "transparent")
        shape_style = f'fill="{html.escape(str(fill))}" stroke="{html.escape(str(stroke))}" stroke-width="2"'

        if element_type == "rectangle":
            parts.append(
                f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
                f'rx="6" {shape_style}/>'
            )
        elif element_type == "ellipse":
            parts.append(
                f'<ellipse cx="{x + width / 2}" cy="{y + height / 2}" '
                f'rx="{width / 2}" ry="{height / 2}" {shape_style}/>'
            )
        elif element_type == "diamond":
            points = (
                f"{x + width / 2},{y} {x + width},{y + height / 2} "
                f"{x + width / 2},{y + height} {x},{y + height / 2}"
            )
            parts.append(f'<polygon points="{points}" {shape_style}/>')
        elif element_type in {"arrow", "line"}:
            marker = ' marker-end="url(#arrowhead)"' if element_type == "arrow" else ""
            parts.append(
                f'<line x1="{x}" y1="{y}" x2="{x + width}" y2="{y + height}" '
                f'stroke="{html.escape(str(stroke))}" stroke-width="2"{marker}/>'
            )

        if element.get("text"):
            text = html.escape(str(element["text"]))
            font_size = element.get("fontSize", 16)
            parts.append(
                f'<text x="{x + width / 2}" y="{y + height / 2}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-size="{font_size}" font-family="sans-serif">{text}</text>'
            )

    body = "\n".join(parts)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">'
        '<defs><marker id="arrowhead" markerWidth="8" markerHeight="8" '
        'refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 z"/>'
        f"</marker></defs>{body}</svg>"
    )


def render_svg(canvas: list[Element], path: str | Path = "canvas.svg") -> Path:
    """Write the current canvas as an SVG file and return its path."""
    output_path = Path(path)
    output_path.write_text(svg_string(canvas), encoding="utf-8")
    return output_path


canvas = [
    {
        "id": "rect_login",
        "type": "rectangle",
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 80,
        "text": "login",
    },
    {
        "id": "rect_database",
        "type": "rectangle",
        "x": 450,
        "y": 100,
        "width": 200,
        "height": 80,
        "text": "database",
    },
    {
        "id": "arrow",
        "type": "arrow",
        "x": 300,
        "y": 135,
        "width": 150,
        "height": 0,
    },

]

result = render_svg(canvas, "rect_login.svg")
