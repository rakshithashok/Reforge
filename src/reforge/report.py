from __future__ import annotations

import json
from pathlib import Path

from reforge.types import MigrationReport


def report_dict(report: MigrationReport) -> dict:
    return {
        "root": str(report.root), "target": report.target,
        "changes": [c.__dict__ for c in report.changes],
        "sites": [s.__dict__ for s in report.sites],
        "verification": report.verification.__dict__ if report.verification else None,
        "human_review": report.human_review,
    }


def write_report(report: MigrationReport, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / "report.json"
    path.write_text(json.dumps(report_dict(report), indent=2), encoding="utf-8")
    return path
