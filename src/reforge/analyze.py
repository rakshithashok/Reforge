"""Static Python analysis used to focus migration and repair work."""

from __future__ import annotations

import ast
from pathlib import Path


def python_files(root: Path) -> list[Path]:
    """Return source files while excluding generated and environment directories."""
    ignored = {".git", ".venv", "venv", "__pycache__", "build", "dist"}
    return sorted(p for p in root.rglob("*.py") if not ignored.intersection(p.parts))


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.symbols: list[dict[str, object]] = []
        self.imports: list[dict[str, object]] = []
        self.calls: list[dict[str, object]] = []
        self._scope: list[str] = []

    def _qualified_name(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._qualified_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return None

    def _definition(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
        qualified = ".".join([*self._scope, node.name])
        self.symbols.append({"name": node.name, "qualified_name": qualified,
                             "line": node.lineno, "kind": type(node).__name__})
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    visit_FunctionDef = _definition
    visit_AsyncFunctionDef = _definition
    visit_ClassDef = _definition

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append({"module": alias.name, "name": None,
                                 "asname": alias.asname, "line": node.lineno})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = "." * node.level + (node.module or "")
        for alias in node.names:
            self.imports.append({"module": module, "name": alias.name,
                                 "asname": alias.asname, "line": node.lineno})

    def visit_Call(self, node: ast.Call) -> None:
        name = self._qualified_name(node.func)
        if name:
            self.calls.append({"callee": name, "line": node.lineno,
                               "scope": ".".join(self._scope) or None})
        self.generic_visit(node)


def analyze_project(root: Path) -> dict[str, dict[str, list[dict[str, object]]]]:
    """Index definitions, imports, and call sites without importing project code."""
    result: dict[str, dict[str, list[dict[str, object]]]] = {}
    for path in python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        visitor = _Visitor()
        visitor.visit(tree)
        result[str(path.relative_to(root))] = {
            "symbols": visitor.symbols,
            "imports": visitor.imports,
            "calls": visitor.calls,
        }
    return result


def analyze(root: Path) -> dict[str, list[dict[str, object]]]:
    """Return definitions in the original compact shape for existing callers."""
    return {path: data["symbols"] for path, data in analyze_project(root).items()}
