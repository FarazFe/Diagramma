import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from agent import MODEL, build_client
from evals.harness import load_cases, run_case
from evals.scorers import SCORERS


def average(values):
    applicable = [value for value in values if value is not None]
    return sum(applicable) / len(applicable) if applicable else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=("baseline", "planning", "focused"),
        default="focused",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(f"evals/results/{args.profile}.json")

    rows = []
    for case in load_cases():
        result = run_case(case, build_client, profile=args.profile)
        scores = {name: scorer(case, result) for name, scorer in SCORERS.items()}
        rows.append({**result, "scores": scores})
        print(case["id"], scores, f"{result['duration_seconds']:.2f}s")
    averages = {name: average([row["scores"][name] for row in rows]) for name in SCORERS}
    print("Averages:", averages)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "profile": args.profile,
        "model": MODEL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
        "averages": averages,
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
