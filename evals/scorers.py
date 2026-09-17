"""Deterministic scorers for diagram-agent evaluation cases."""

from __future__ import annotations

import re
from typing import Any, Callable

from canvas import validate_element

Score = float | None


def _label_matches(expected: str, actual: str) -> bool:
    expected_words = expected.strip().lower().split()
    actual_words = actual.strip().lower().split()
    return all(
        any(
            expected_word == actual_word
            or (
                min(len(expected_word), len(actual_word)) >= 5
                and (
                    expected_word.startswith(actual_word[:5])
                    or actual_word.startswith(expected_word[:5])
                )
            )
            for actual_word in actual_words
        )
        for expected_word in expected_words
    )


def schema_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    canvas = result["canvas"]
    if not canvas:
        return None if case.get("category") == "edge" else 0.0
    return sum(validate_element(element) is None for element in canvas) / len(canvas)


def structure_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    checks: list[bool] = []
    canvas = result["canvas"]
    labels = [str(element.get("text", "")) for element in canvas]
    for expected in case.get("expectedLabels", []):
        checks.append(any(_label_matches(str(expected), label) for label in labels))
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


def connection_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    expected = case.get("expectedConnections")
    if not expected:
        return None

    labels_by_id = {
        element.get("id"): str(element.get("text", "")).strip().lower()
        for element in result["canvas"]
        if element.get("type") not in {"arrow", "line"}
    }
    actual = {
        (
            labels_by_id.get(element.get("sourceId"), ""),
            labels_by_id.get(element.get("targetId"), ""),
        )
        for element in result["canvas"]
        if element.get("type") == "arrow"
    }
    matched = 0
    for connection in expected:
        if any(
            _label_matches(connection["source"], source)
            and _label_matches(connection["target"], target)
            for source, target in actual
        ):
            matched += 1
    return matched / len(expected)


def error_handling_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    if case.get("expectedOutcome") != "missing_target":
        return None
    reply = result["reply"].lower()
    phrases = ("not found", "missing", "couldn't find", "no element", "cannot find", "unknown")
    explains_failure = any(phrase in reply for phrase in phrases)
    seed = case.get("seed", {}).get("elements", [])
    canvas_unchanged = result["canvas"] == seed
    return (float(explains_failure) + float(canvas_unchanged)) / 2


def edge_behavior_score(case: dict[str, Any], result: dict[str, Any]) -> Score:
    outcome = case.get("expectedOutcome")
    if outcome == "empty_canvas":
        return 1.0 if not result["canvas"] else 0.0
    if outcome == "all_elements_updated":
        expected_updates = case.get("expectedUpdates", {})
        preserved_ids = case.get("preservedIds", [])
        elements_by_id = {element.get("id"): element for element in result["canvas"]}
        checks = [
            element_id in elements_by_id
            and all(
                elements_by_id[element_id].get(field) == expected
                for field, expected in expected_updates.items()
            )
            for element_id in preserved_ids
        ]
        return sum(checks) / len(checks) if checks else 0.0
    return None


SCORERS: dict[str, Callable[[dict[str, Any], dict[str, Any]], Score]] = {
    "Schema": schema_score,
    "Structure": structure_score,
    "Preservation": preservation_score,
    "Keywords": keyword_score,
    "Connections": connection_score,
    "ErrorHandling": error_handling_score,
    "EdgeBehavior": edge_behavior_score,
}
