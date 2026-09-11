"""Small manual CLI for exercising the Stage 2 canvas tools."""

from __future__ import annotations

import json

from canvas import Element
from tools import make_tool_functions


def print_canvas(canvas: list[Element]) -> None:
    print(json.dumps(canvas, indent=2))


def main() -> None:
    canvas: list[Element] = []
    tool_functions = make_tool_functions(canvas)

    print("Stage 2 playground")
    print("Commands: sample, modify <id> <json>, show, clear, quit")

    while True:
        try:
            command = input("canvas> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if command in {"quit", "exit"}:
            break
        if command == "sample":
            result = tool_functions["generate_diagram"]({
                "elements": [
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
                ]
            })
            print(result)
            print_canvas(canvas)
            continue
        if command == "show":
            print_canvas(canvas)
            continue
        if command == "clear":
            canvas.clear()
            print("Canvas cleared.")
            continue
        if command.startswith("modify "):
            parts = command.split(maxsplit=2)
            if len(parts) != 3:
                print('Usage: modify <id> {"field": "value"}')
                continue
            try:
                updates = json.loads(parts[2])
            except json.JSONDecodeError as error:
                print(f"Invalid JSON: {error}")
                continue
            print(tool_functions["modify_diagram"]({
                "element_id": parts[1],
                "updates": updates,
            }))
            print_canvas(canvas)
            continue
        print("Unknown command.")


if __name__ == "__main__":
    main()
