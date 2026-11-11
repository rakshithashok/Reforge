from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Change:
    path: str
    before: str
    after: str
    provenance: str


@dataclass
class Site:
    path: str
    line: int
    rule_id: str
    description: str


@dataclass
class VerificationResult:
    passed: bool
    exit_code: int | None
    output: str
    duration_seconds: float
    coverage: float | None = None


@dataclass
class MigrationReport:
    root: Path
    target: str
    changes: list[Change] = field(default_factory=list)
    sites: list[Site] = field(default_factory=list)
    verification: VerificationResult | None = None
    human_review: list[str] = field(default_factory=list)
