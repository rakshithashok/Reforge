from __future__ import annotations

from pathlib import Path

from reforge.analyze import analyze, python_files
from reforge.audit import (
    change_size,
    coverage_not_dropped,
    is_test_file,
    minimal_diff_ok,
    test_snapshot,
    tests_unchanged,
)
from reforge.rules.sqlalchemy import SQLAlchemy20Rule
from reforge.types import Change, MigrationReport
from reforge.verify import verify


def migrate(root: Path, target: str = "sqlalchemy-2.0", apply: bool = False) -> MigrationReport:
    if not root.is_dir():
        raise ValueError(f"Repository does not exist: {root}")
    if target != "sqlalchemy-2.0":
        raise ValueError(f"Unsupported target: {target}")
    _symbols = analyze(root)
    rule = SQLAlchemy20Rule()
    report = MigrationReport(root=root.resolve(), target=target)
    # Snapshot is taken before changes so callers can enforce test immutability.
    original_tests = test_snapshot(root)
    for path in python_files(root):
        if is_test_file(path):
            continue
        try:
            before = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        after, sites = rule.transform(path.relative_to(root), before)
        report.sites.extend(sites)
        if before != after:
            report.changes.append(Change(str(path.relative_to(root)), before, after, rule.rule_id))
            if apply:
                path.write_text(after, encoding="utf-8")
    if apply and test_snapshot(root) != original_tests:
        for change in report.changes:
            (root / change.path).write_text(change.before, encoding="utf-8")
        raise RuntimeError("Migration touched test files; changes were reverted")
    return report


def migrate_verified(root: Path, config: dict, target: str = "sqlalchemy-2.0") -> MigrationReport:
    """Apply rules only when baseline and candidate checks satisfy every guard."""
    original_tests = test_snapshot(root)
    baseline = verify(root, config, collect_coverage=True)
    report = migrate(root, target=target, apply=True)
    candidate = verify(root, config, collect_coverage=True)
    report.verification = candidate
    changed_lines = sum(change_size(change.before, change.after) for change in report.changes)
    max_ratio = float(config.get("repair", {}).get("minimal_diff_ratio", 4.0))
    violations: list[str] = []
    if not baseline.passed:
        violations.append("Original repository verification failed")
    if not candidate.passed:
        violations.append("Migrated repository verification failed")
    if not tests_unchanged(root, original_tests):
        violations.append("Migration modified test files")
    if not coverage_not_dropped(baseline.coverage, candidate.coverage):
        violations.append("Coverage did not meet the baseline")
    if not minimal_diff_ok(changed_lines, len(report.sites), max_ratio):
        violations.append("Migration exceeded the minimal-diff guard")
    if violations:
        for change in report.changes:
            (root / change.path).write_text(change.before, encoding="utf-8")
        report.human_review.extend(violations)
    return report
