# Diagram Agent Evaluation

The evaluation suite contains 18 cases: 5 create, 5 modify, 4 domain, and 4 edge cases. It uses the same `run_turn()` loop as the CLI, seeds private canvases for modification cases, records duration, and applies deterministic scorers.

## Measured runs

| Profile | Structure | Connections | Preservation | ErrorHandling | Average duration |
|---|---:|---:|---:|---:|---:|
| Baseline | 100% | 0% | 100% | 25% | 5.18s |
| Planning only | 95.6% | 0% | 100% | 25% | 9.61s |
| Planning + focused connections | 97.2% | 90.7% | 100% | 25% | 10.20s |
| Final focused + edge preflight | 100% | 92.6% | 100% | 100% | 8.28s |

The focused connection technique moved Connections from `0%` to `90.7%` by separating node creation from relationships. The `connect_elements` tool receives source and target IDs; Python calculates arrow endpoints and stores `sourceId` and `targetId`. The final run reached `92.6%`; the remaining variation came from one OAuth case choosing a different valid topology than the handwritten expectation.

Planning alone was a dud for the measured target: Connections stayed at `0%`, Structure decreased from `100%` to `95.6%`, and average duration increased from `5.18s` to `9.61s`. The extra planning call did not help while the model still had to emit raw-coordinate arrows.

The final edge improvement added deterministic preflight handling. Empty-canvas modification requests now return a clear missing-element response without an API call, and explicit empty-diagram requests preserve an empty canvas. The edge suite moved ErrorHandling from `25%` to `100%` and EdgeBehavior from `50%` to `100%`.

## Reproduce

```bash
/home/faraz/projects/gen-ai/venv/bin/python -m evals.run_eval --profile baseline --output evals/results/profile_baseline.json
/home/faraz/projects/gen-ai/venv/bin/python -m evals.run_eval --profile planning --output evals/results/profile_planning.json
/home/faraz/projects/gen-ai/venv/bin/python -m evals.run_eval --profile focused --output evals/results/profile_focused.json
```

The final artifacts are stored under `evals/results/`. These commands call AvalAI and may incur API usage.

## Optional Excalidraw export

The CLI also writes `canvas.excalidraw` after each turn. This is an editable Excalidraw scene generated from the same canonical canvas; it does not change the required `canvas.svg` output or evaluation path.
