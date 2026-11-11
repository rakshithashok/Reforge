from __future__ import annotations

import json
from pathlib import Path


def render(results: Path) -> str:
    data = json.loads((results / "benchmark.json").read_text(encoding="utf-8"))
    summary = data["summary"]
    return (f"Arm: {data['arm']}\nRepositories: {summary['repositories']}\n"
            f"Test pass rate: {summary['test_pass_rate']}\n"
            f"Mean cost: {summary['mean_cost_usd']}\n")
