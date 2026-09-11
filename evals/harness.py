from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

from agent import run_turn
from canvas import Element


def load_cases(path: str | Path = "evals/golden.json") -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_case(case: dict[str, Any], client_factory: Callable[[], Any]) -> dict[str, Any]:
    seeded = case.get("seed", {}).get("elements", [])
    canvas: list[Element] = [dict(element) for element in seeded]
    messages = [{"role": "system", "content": "You are a diagram design assistant."}, {"role": "user", "content": case["input"]}]
    started_at = time.perf_counter()
    reply = run_turn(messages, canvas, client=client_factory())
    return {"id": case["id"], "category": case["category"], "reply": reply, "canvas": canvas, "duration_seconds": time.perf_counter() - started_at}

