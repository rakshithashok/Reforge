"""Lightweight project analysis; richer symbol and call graphs are future work."""

from __future__ import annotations

import ast
from pathlib import Path


def python_files(root: Path) -> list[Path]:
    ignored = {".git", ".venv", "venv", "__pycache__", "build", "dist"}
    return sorted(p for p in root.rglob("*.py") if not ignored.intersection(p.parts))


def analyze(root: Path) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for path in python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        symbols = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append({"name": node.name, "line": node.lineno, "kind": type(node).__name__})
        result[str(path.relative_to(root))] = symbols
    return result
