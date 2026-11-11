from __future__ import annotations

from pathlib import Path


def build_prompt(root: Path, failing_output: str, sites: list[dict[str, object]]) -> str:
    excerpts = []
    for site in sites:
        path = root / str(site["path"])
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            line = max(1, int(site.get("line", 1)))
            excerpts.append(f"{path}:{line}\n" + "\n".join(lines[max(0, line - 4):line + 3]))
    return "Repair only the migration failures. Return a unified diff; do not edit tests.\n\n" + \
        "Affected sites:\n" + "\n\n".join(excerpts) + \
        "\n\nVerification output:\n" + failing_output[-12000:]
