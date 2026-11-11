from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trial:
    repository: str
    arm: str
    test_passed: bool
    build_succeeded: bool
    guard_violations: int
    cost_usd: float | None
    latency_seconds: float
    changed_lines: int


def summarize(trials: list[Trial]) -> dict[str, float | int | None]:
    count = len(trials)
    if not count:
        return {"repositories": 0, "test_pass_rate": None, "build_success": None,
                "guard_violations": 0, "mean_cost_usd": None, "p95_latency_seconds": None}
    latencies = sorted(t.latency_seconds for t in trials)
    costs = [t.cost_usd for t in trials if t.cost_usd is not None]
    return {
        "repositories": count,
        "test_pass_rate": sum(t.test_passed for t in trials) / count,
        "build_success": sum(t.build_succeeded for t in trials) / count,
        "guard_violations": sum(t.guard_violations for t in trials),
        "mean_cost_usd": sum(costs) / len(costs) if costs else None,
        "p95_latency_seconds": latencies[min(len(latencies) - 1, int(.95 * len(latencies)))],
    }
