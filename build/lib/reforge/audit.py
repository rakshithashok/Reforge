from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def test_snapshot(root: Path) -> dict[str, str]:
    files = sorted(p for p in root.rglob("*") if p.is_file() and is_test_file(p))
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def is_test_file(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py") or "tests" in path.parts


def tests_unchanged(root: Path, original: dict[str, str]) -> bool:
    return test_snapshot(root) == original


def diff_size(root: Path) -> int:
    result = subprocess.run(["git", "-C", str(root), "diff", "--numstat"], capture_output=True, text=True)
    if result.returncode:
        return 0
    total = 0
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2 and fields[0].isdigit() and fields[1].isdigit():
            total += int(fields[0]) + int(fields[1])
    return total


def coverage_percent(path: Path) -> float | None:
    """Read coverage.py JSON output and return the total covered percentage."""
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = data.get("totals", {})
    value = totals.get("percent_covered")
    return float(value) if value is not None else None


def minimal_diff_ok(changed_lines: int, affected_sites: int, max_ratio: float = 4.0) -> bool:
    if changed_lines < 0 or affected_sites < 0:
        return False
    if changed_lines == 0:
        return True
    return affected_sites > 0 and changed_lines <= affected_sites * max_ratio


def coverage_not_dropped(original: float | None, candidate: float | None) -> bool:
    # Missing measurements cannot establish the guard; callers should treat it
    # as an unavailable check and require an explicit policy decision.
    return original is not None and candidate is not None and candidate >= original


# These public helpers intentionally begin with ``test`` because they operate
# on test files.  Prevent pytest from collecting them when a test module
# imports them directly.
test_snapshot.__test__ = False
tests_unchanged.__test__ = False
