from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml

from bench.metrics import Trial, summarize


def run(manifest: Path, config: Path, output: Path = Path("results")) -> None:
    corpus = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    repositories = corpus.get("repositories", [])
    arm_config = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    trials: list[Trial] = []
    # No repositories or model providers are silently synthesized. Populate the
    # manifest and configure runners before interpreting results as a benchmark.
    for record in repositories:
        if not all(key in record for key in ("name", "url", "commit", "test_command")):
            raise ValueError(f"Incomplete corpus entry: {record!r}")
        raise NotImplementedError("Repository checkout and arm execution are not configured yet")
    output.mkdir(parents=True, exist_ok=True)
    (output / "benchmark.json").write_text(json.dumps({
        "arm": arm_config.get("arm", "unknown"),
        "manifest": str(manifest),
        "summary": summarize(trials),
        "trials": [t.__dict__ for t in trials],
    }, indent=2), encoding="utf-8")
    with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(Trial.__dataclass_fields__))
        writer.writeheader()
    print(f"No benchmark trials were run; wrote empty artifacts to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    run(args.manifest, args.config, args.output)


if __name__ == "__main__":
    main()
