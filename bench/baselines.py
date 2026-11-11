"""Adapters for comparable external migration tools.

Each adapter must pin its version, execute in an isolated runner, and return a
Trial using the same verification command as Reforge. This module deliberately
does not download or launch third-party tools by itself.
"""

from __future__ import annotations

from typing import Protocol

from bench.metrics import Trial


class Baseline(Protocol):
    name: str

    def run(self, repository: str, commit: str, test_command: list[str]) -> Trial: ...


class UnconfiguredBaseline:
    def __init__(self, name: str) -> None:
        self.name = name

    def run(self, repository: str, commit: str, test_command: list[str]) -> Trial:
        raise NotImplementedError(f"Baseline {self.name!r} has no pinned adapter configured")
