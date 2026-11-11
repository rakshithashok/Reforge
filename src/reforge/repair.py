"""Bounded, test-preserving application of model-proposed Git patches."""

from __future__ import annotations

import subprocess
from pathlib import Path

from reforge.audit import is_test_file, test_snapshot, tests_unchanged
from reforge.models.base import Model
from reforge.types import VerificationResult
from reforge.verify import verify


def repair_loop(model: Model, prompt: str, max_iterations: int = 3) -> list[str]:
    """Request distinct patch proposals without applying them."""
    proposals: list[str] = []
    seen: set[str] = set()
    for _ in range(max_iterations):
        response = model.propose(prompt)
        if not response.patch or response.patch in seen:
            break
        proposals.append(response.patch)
        seen.add(response.patch)
        prompt += "\n\nPrevious patch failed. Produce a different minimal patch."
    return proposals


def _patch_paths(patch: str) -> set[Path]:
    paths: set[Path] = set()
    for line in patch.splitlines():
        if not line.startswith("+++ "):
            continue
        value = line[4:].strip()
        if value == "/dev/null":
            continue
        value = value.removeprefix("b/")
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Patch contains an unsafe path")
        paths.add(path)
    if not paths:
        raise ValueError("Patch contains no file changes")
    return paths


def apply_patch(root: Path, patch: str) -> None:
    """Apply a Git-style patch after rejecting every test-file modification."""
    paths = _patch_paths(patch)
    if any(is_test_file(path) for path in paths):
        raise ValueError("Model patches may not modify test files")
    checked = subprocess.run(["git", "-C", str(root), "apply", "--check", "--whitespace=nowarn", "-"],
                             input=patch, text=True, capture_output=True, check=False)
    if checked.returncode:
        raise ValueError(checked.stderr.strip() or "Patch does not apply")
    applied = subprocess.run(["git", "-C", str(root), "apply", "--whitespace=nowarn", "-"],
                             input=patch, text=True, capture_output=True, check=False)
    if applied.returncode:
        raise RuntimeError(applied.stderr.strip() or "Patch could not be applied")


def repair_and_verify(root: Path, model: Model, prompt: str, config: dict,
                      max_iterations: int = 3) -> VerificationResult | None:
    """Apply the first verified proposal, reversing failed candidates immediately."""
    original_tests = test_snapshot(root)
    for patch in repair_loop(model, prompt, max_iterations):
        apply_patch(root, patch)
        if not tests_unchanged(root, original_tests):
            raise RuntimeError("Patch modified tests despite validation")
        result = verify(root, config)
        if result.passed:
            return result
        reversed_patch = subprocess.run(
            ["git", "-C", str(root), "apply", "--reverse", "--whitespace=nowarn", "-"],
            input=patch, text=True, capture_output=True, check=False,
        )
        if reversed_patch.returncode:
            raise RuntimeError("Failed to revert an unverified model patch")
    return None
