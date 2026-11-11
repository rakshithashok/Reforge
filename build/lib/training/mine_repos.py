"""Validate and normalize externally collected migration repository records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(records: list[dict]) -> list[dict]:
    required = {"name", "url", "commit", "license", "migration_commit", "test_command"}
    accepted = []
    for record in records:
        missing = required - record.keys()
        if missing:
            raise ValueError(f"{record.get('name', '<unnamed>')} missing {sorted(missing)}")
        if not record["commit"] or not record["migration_commit"]:
            raise ValueError("Repository and migration commits must be pinned")
        accepted.append(record)
    return accepted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    records = validate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(records, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
