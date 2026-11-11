"""Validate records and mine pinned SQLAlchemy migration commits from Git repositories."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REQUIRED_FIELDS = {"name", "url", "commit", "license", "migration_commit", "test_command"}
MIGRATION_MARKERS = ("sqlalchemy", "session.query", "query(", "select([", "declarative_base")


def validate(records: list[dict]) -> list[dict]:
    """Validate corpus records and normalize test commands to argument lists."""
    accepted = []
    for record in records:
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            raise ValueError(f"{record.get('name', '<unnamed>')} missing {sorted(missing)}")
        if not record["commit"] or not record["migration_commit"]:
            raise ValueError("Repository and migration commits must be pinned")
        normalized = dict(record)
        if isinstance(normalized["test_command"], str):
            normalized["test_command"] = normalized["test_command"].split()
        if not isinstance(normalized["test_command"], list) or not normalized["test_command"]:
            raise ValueError(f"{record['name']} has no usable test command")
        accepted.append(normalized)
    return accepted


def _git(repository: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repository), *args], capture_output=True,
                            text=True, check=False)
    if result.returncode:
        message = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"git {' '.join(args)} failed for {repository}: {message}")
    return result.stdout.strip()


def _remote_url(repository: Path) -> str:
    try:
        return _git(repository, "remote", "get-url", "origin")
    except ValueError:
        return str(repository.resolve())


def _candidate_patch(patch: str) -> bool:
    lowered = patch.lower()
    return "sqlalchemy" in lowered and any(marker in lowered for marker in MIGRATION_MARKERS[1:])


def mine(repository: Path, license_name: str, test_command: list[str], limit: int = 200) -> list[dict]:
    """Find commits whose diffs contain SQLAlchemy migration signals.

    The returned ``commit`` is the parent revision used as a reproducible
    pre-migration checkout. ``migration_commit`` is the maintainer's follow-up
    revision, suitable for extracting a supervised training pair.
    """
    if not repository.is_dir():
        raise ValueError(f"Repository does not exist: {repository}")
    commits = _git(repository, "log", f"--max-count={limit}", "--format=%H").splitlines()
    records: list[dict] = []
    for commit in commits:
        parents = _git(repository, "rev-list", "--parents", "-n", "1", commit).split()
        if len(parents) != 2:
            continue
        parent = parents[1]
        patch = _git(repository, "diff", "--no-ext-diff", "--unified=0", parent, commit)
        if not _candidate_patch(patch):
            continue
        records.append({
            "name": repository.name,
            "url": _remote_url(repository),
            "commit": parent,
            "license": license_name,
            "migration_commit": commit,
            "test_command": list(test_command),
        })
    return validate(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", help="JSON records to validate")
    parser.add_argument("output", type=Path, nargs="?", help="Destination JSON file")
    parser.add_argument("--scan", type=Path, metavar="REPOSITORY",
                        help="Mine a local Git checkout instead of validating JSON")
    parser.add_argument("--output", dest="scan_output", type=Path,
                        help="Destination JSON file when using --scan")
    parser.add_argument("--license", dest="license_name",
                        help="Verified SPDX license for the scanned repository")
    parser.add_argument("--limit", type=int, default=200, help="Maximum commits to inspect")
    parser.add_argument("--test-command", nargs=argparse.REMAINDER,
                        help="Repository test command; place this option last")
    args = parser.parse_args()

    if args.scan:
        if not args.scan_output or not args.license_name or not args.test_command:
            parser.error("--scan requires --output, --license, and --test-command")
        records = mine(args.scan, args.license_name, args.test_command, args.limit)
        args.scan_output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        print(f"Found {len(records)} migration commit(s)")
        return
    if not args.input or not args.output:
        parser.error("input and output are required unless --scan is used")
    records = validate(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
