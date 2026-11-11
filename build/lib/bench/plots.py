"""Plot measured benchmark trials when matplotlib is installed."""

from __future__ import annotations

import json
from pathlib import Path


def pareto(results: Path, output: Path | None = None) -> Path | None:
    data = json.loads((results / "benchmark.json").read_text(encoding="utf-8"))
    trials = [t for t in data.get("trials", []) if t.get("cost_usd") is not None]
    if not trials:
        return None
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Install matplotlib to generate Pareto plots") from exc
    destination = output or results / "pareto.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    arms = sorted({t["arm"] for t in trials})
    for arm in arms:
        rows = [t for t in trials if t["arm"] == arm]
        rate = sum(bool(t["test_passed"]) for t in rows) / len(rows)
        cost = sum(t["cost_usd"] for t in rows) / len(rows)
        plt.scatter(cost, rate, label=arm)
    plt.xlabel("Mean cost per repository (USD)")
    plt.ylabel("Original test pass rate")
    plt.ylim(0, 1)
    plt.legend()
    plt.tight_layout()
    plt.savefig(destination, dpi=160)
    plt.close()
    return destination
