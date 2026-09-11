import json
from pathlib import Path

from agent import build_client
from evals.harness import load_cases, run_case
from evals.scorers import SCORERS


def average(values):
    applicable = [value for value in values if value is not None]
    return sum(applicable) / len(applicable) if applicable else None


def main():
    rows = []
    for case in load_cases():
        result = run_case(case, build_client)
        scores = {name: scorer(case, result) for name, scorer in SCORERS.items()}
        rows.append({**result, "scores": scores})
        print(case["id"], scores, f"{result['duration_seconds']:.2f}s")
    averages = {name: average([row["scores"][name] for row in rows]) for name in SCORERS}
    print("Averages:", averages)
    output = Path("evals/results/latest.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"rows": rows, "averages": averages}, indent=2), encoding="utf-8")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
