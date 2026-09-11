"""Deterministic scorers for diagram-agent evaluation cases."""

from __future__ import annotations

import re
from typing import Any, Callable

from canvas import validate_element

Score = float | None


def schema_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    canvas = result["canvas"]
    if not canvas:
        return None if case.get("category") == "edge" else 0.0
    return sum(validate_element(element) is None for element in canvas) / len(canvas)


def structure_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    checks: list[bool] = []
    canvas = result["canvas"]
    labels = {str(element.get("text", "")).strip().lower() for element in canvas}
    for expected in case.get("expectedLabels", []):
        checks.append(str(expected).strip().lower() in labels)
    for element_type, minimum in case.get("expectedCounts", {}).items():
        actual = sum(element.get("type") == element_type for element in canvas)
        checks.append(actual >= int(minimum))
    return sum(checks) / len(checks) if checks else None


def preservation_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    expected_ids = case.get("preservedIds")
    if not expected_ids:
        return None
    final_ids = {element.get("id") for element in result["canvas"]}
    return sum(element_id in final_ids for element_id in expected_ids) / len(expected_ids)


def keyword_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    keywords = case.get("keywords")
    if not keywords:
        return None
    text = " ".join([result["reply"], *(str(element.get("text", "")) for element in result["canvas"])]).lower()
    return sum(keyword.lower() in text for keyword in keywords) / len(keywords)


def error_handling_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    if case.get("category") != "edge":
        return None
    reply = result["reply"].lower()
    behavior = case.get("expectedBehavior", "clear error explanation").lower()
    if "empty" in behavior:
        return 1.0 if not result["canvas"] else 0.0
    phrases = ("not found", "missing", "couldn't find", "no element", "cannot find", "unknown")
    return 1.0 if any(phrase in reply for phrase in phrases) else 0.0


SCORERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], Score]] = {
    "Schema": schema_score,
    "Structure": structure_score,
    "Preservation": preservation_score,
    "Keywords": keyword_score,
    "ErrorHandling": error_handling_score,
}
