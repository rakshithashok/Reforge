"""Initial exact SQLAlchemy 1.x to 2.0 codemod set."""

from __future__ import annotations

from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

from reforge.types import Site


class _QueryGetTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.sites: list[Site] = []

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:
        # session.query(Model).get(key) -> session.get(Model, key)
        outer = updated_node.func
        query_call = outer.value if isinstance(outer, cst.Attribute) and outer.attr.value == "get" else None
        if not isinstance(query_call, cst.Call) or not isinstance(query_call.func, cst.Attribute):
            return updated_node
        if query_call.func.attr.value != "query" or len(query_call.args) != 1:
            return updated_node
        if not isinstance(original_node.func, cst.Attribute):
            return updated_node
        key_args = list(updated_node.args)
        if not key_args:
            return updated_node
        session = query_call.func.value
        model_args = query_call.args
        replacement = cst.Call(
            func=cst.Attribute(value=session, attr=cst.Name("get")),
            args=[*model_args, *key_args],
        )
        line = self.get_metadata(PositionProvider, original_node).start.line
        self.sites.append(Site(self.relative_path, line, "SA20_QUERY_GET", "Use Session.get"))
        return replacement


class SQLAlchemy20Rule:
    rule_id = "sqlalchemy-2.0"

    def transform(self, path: Path, source: str) -> tuple[str, list[Site]]:
        relative_path = str(path)
        module = cst.parse_module(source)
        transformer = _QueryGetTransformer(relative_path)
        changed = MetadataWrapper(module).visit(transformer)
        return changed.code, transformer.sites
