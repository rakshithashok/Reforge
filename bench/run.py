"""Run reproducible rules-only benchmark trials from a pinned corpus manifest."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

from bench.metrics import Trial, summarize
from reforge.audit import (
    change_size,
    coverage_not_dropped,
    minimal_diff_ok,
    test_snapshot,
    tests_unchanged,
)
from reforge.pipeline import migrate
from reforge.verify import verify


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in {path}")  # noqa: TRY004
    return data


def _command(value: object) -> list[str]:
    if isinstance(value, str):
        return value.split()
    if isinstance(value, list) and all(isinstance(part, str) for part in value) and value:
        return value
    raise ValueError("Corpus test_command must be a non-empty string or list of strings")


def _coverage_command(record: dict[str, Any]) -> list[str] | None:
    value = record.get("coverage_command")
    return _command(value) if value is not None else None


def _checkout(record: dict[str, Any], destination: Path) -> None:
    url, commit = str(record["url"]), str(record["commit"])
    subprocess.run(["git", "clone", "--no-checkout", url, str(destination)], check=True,
                   capture_output=True, text=True)
    subprocess.run(["git", "-C", str(destination), "checkout", "--detach", commit], check=True,
                   capture_output=True, text=True)


def _pipeline_config(config_path: Path, arm: dict[str, Any]) -> dict[str, Any]:
    configured = arm.get("pipeline")
    if not configured:
        return {}
    path = (config_path.parent / str(configured)).resolve()
    return _load_yaml(path)


def _repository_config(pipeline_config: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    """Apply a record-specific prebuilt sandbox image without mutating shared config."""
    image = record.get("docker_image")
    if not image:
        return pipeline_config
    configured = dict(pipeline_config)
    verification = dict(configured.get("verification", {}))
    verification["docker_image"] = str(image)
    configured["verification"] = verification
    return configured


def run_trial(record: dict[str, Any], arm: dict[str, Any], pipeline_config: dict[str, Any]) -> Trial:
    """Check out one immutable source revision and measure its rules-only migration."""
    required = {"name", "url", "commit", "test_command"}
    missing = required - record.keys()
    if missing:
        raise ValueError(f"Incomplete corpus entry: missing {sorted(missing)}")
    arm_name = str(arm.get("arm", "rules_only"))
    if arm_name != "rules_only":
        raise ValueError(f"Arm {arm_name!r} requires a configured model or baseline adapter")
    repository_config = _repository_config(pipeline_config, record)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="reforge-bench-") as directory:
        repository = Path(directory) / "repository"
        _checkout(record, repository)
        original_tests = test_snapshot(repository)
        test_command = _command(record["test_command"])
        coverage_command = _coverage_command(record)
        baseline = verify(repository, repository_config, test_command)
        baseline_coverage = verify(repository, repository_config, collect_coverage=True,
                                   coverage_command=coverage_command)
        report = migrate(repository, target=str(arm.get("rules", repository_config.get("target", "sqlalchemy-2.0"))),
                         apply=True)
        changed_lines = sum(change_size(change.before, change.after) for change in report.changes)
        guard_violations = 0
        if not tests_unchanged(repository, original_tests):
            guard_violations += 1
        ratio = float(repository_config.get("repair", {}).get("minimal_diff_ratio", 4.0))
        if not minimal_diff_ok(changed_lines, len(report.sites), ratio):
            guard_violations += 1
        verification = verify(repository, repository_config, test_command)
        candidate_coverage = verify(repository, repository_config, collect_coverage=True,
                                    coverage_command=coverage_command)
        if not baseline_coverage.passed or not candidate_coverage.passed:
            guard_violations += 1
        if not coverage_not_dropped(baseline_coverage.coverage, candidate_coverage.coverage):
            guard_violations += 1
        return Trial(
            repository=str(record["name"]),
            arm=arm_name,
            test_passed=baseline.passed and verification.passed and guard_violations == 0,
            build_succeeded=baseline.passed and verification.passed,
            guard_violations=guard_violations,
            cost_usd=0.0,
            latency_seconds=time.monotonic() - started,
            changed_lines=changed_lines,
        )


def write_results(manifest: Path, arm: dict[str, Any], trials: list[Trial], output: Path,
                  failures: list[dict[str, str]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark.json").write_text(json.dumps({
        "arm": arm.get("arm", "unknown"),
        "manifest": str(manifest),
        "summary": summarize(trials),
        "trials": [trial.__dict__ for trial in trials],
        "failures": failures,
    }, indent=2) + "\n", encoding="utf-8")
    with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(Trial.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(trial.__dict__ for trial in trials)


def run(manifest: Path, config: Path, output: Path = Path("results")) -> list[Trial]:
    corpus = _load_yaml(manifest)
    repositories = corpus.get("repositories", [])
    if not isinstance(repositories, list):
        raise ValueError("Corpus repositories must be a list")  # noqa: TRY004
    arm = _load_yaml(config)
    pipeline_config = _pipeline_config(config, arm)
    trials: list[Trial] = []
    failures: list[dict[str, str]] = []
    for record in repositories:
        started = time.monotonic()
        try:
            trials.append(run_trial(record, arm, pipeline_config))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            name = str(record.get("name", "<unnamed>")) if isinstance(record, dict) else "<invalid>"
            trials.append(Trial(name, str(arm.get("arm", "unknown")), False, False, 1, None,
                                time.monotonic() - started, 0))
            failures.append({"repository": name, "error": str(exc)})
    write_results(manifest, arm, trials, output, failures)
    print(f"Ran {len(trials)} {arm.get('arm', 'unknown')} trial(s); artifacts: {output}")
    return trials


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    run(args.manifest, args.config, args.output)


if __name__ == "__main__":
    main()
