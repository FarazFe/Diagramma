"""Reapply current deterministic scorers to a saved evaluation run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.harness import load_cases
from evals.scorers import SCORERS


def average(values: list[float | None]) -> float | None:
    applicable = [value for value in values if value is not None]
    return sum(applicable) / len(applicable) if applicable else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    cases_by_id = {case["id"]: case for case in load_cases()}
    data = json.loads(args.input.read_text(encoding="utf-8"))
    rows = data["rows"]

    for row in rows:
        case = cases_by_id[row["id"]]
        row["scores"] = {
            name: scorer(case, row) for name, scorer in SCORERS.items()
        }

    averages = {
        name: average([row["scores"][name] for row in rows])
        for name in SCORERS
    }
    args.output.write_text(
        json.dumps({"rows": rows, "averages": averages}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(averages, indent=2))


if __name__ == "__main__":
    main()
