from __future__ import annotations

from pathlib import Path

from reforge.analyze import analyze, python_files
from reforge.audit import test_snapshot
from reforge.rules.sqlalchemy import SQLAlchemy20Rule
from reforge.types import Change, MigrationReport


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
