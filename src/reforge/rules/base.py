from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from reforge.types import Change, Site


class MigrationRule(Protocol):
    rule_id: str

    def transform(self, path: Path, source: str) -> tuple[str, list[Site]]: ...


@dataclass
class RuleResult:
    changes: list[Change]
    sites: list[Site]
