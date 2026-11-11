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
        if (isinstance(query_call, cst.Call) and isinstance(query_call.func, cst.Attribute)
                and query_call.func.attr.value == "query" and len(query_call.args) == 1):
            key_args = list(updated_node.args)
            if key_args and isinstance(original_node.func, cst.Attribute):
                session = query_call.func.value
                replacement = cst.Call(
                    func=cst.Attribute(value=session, attr=cst.Name("get")),
                    args=[*query_call.args, *key_args],
                )
                self._site(original_node, "SA20_QUERY_GET", "Use Session.get")
                return replacement

        function = self._function_name(updated_node.func)
        if function == "select":
            replacement = self._expand_legacy_list(updated_node)
            if replacement:
                self._site(original_node, "SA20_SELECT_LIST", "Pass select entities directly")
                return replacement
        if function == "case":
            replacement = self._expand_legacy_list(updated_node)
            if replacement:
                self._site(original_node, "SA20_CASE_LIST", "Pass case whens directly")
                return replacement
        return updated_node

    @staticmethod
    def _function_name(function: cst.BaseExpression) -> str | None:
        if isinstance(function, cst.Name):
            return function.value
        if isinstance(function, cst.Attribute):
            return function.attr.value
        return None

    @staticmethod
    def _expand_legacy_list(call: cst.Call) -> cst.Call | None:
        if not call.args or call.args[0].keyword or not isinstance(call.args[0].value, cst.List):
            return None
        items = call.args[0].value.elements
        if not items or any(item is None or isinstance(item, cst.StarredElement) for item in items):
            return None
        expanded = [cst.Arg(value=item.value, comma=item.comma) for item in items if item]
        return call.with_changes(args=[*expanded, *call.args[1:]])

    def _site(self, node: cst.Call, rule_id: str, description: str) -> None:
        line = self.get_metadata(PositionProvider, node).start.line
        self.sites.append(Site(self.relative_path, line, rule_id, description))


class SQLAlchemy20Rule:
    rule_id = "sqlalchemy-2.0"

    def transform(self, path: Path, source: str) -> tuple[str, list[Site]]:
        relative_path = str(path)
        module = cst.parse_module(source)
        transformer = _QueryGetTransformer(relative_path)
        changed = MetadataWrapper(module).visit(transformer)
        return changed.code, transformer.sites
