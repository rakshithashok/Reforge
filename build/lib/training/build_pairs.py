from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def diff_pair(repository: Path, before: str, after: str) -> dict[str, str]:
    source = subprocess.run(["git", "-C", str(repository), "diff", "--no-ext-diff",
                             "--unified=3", before, after], capture_output=True, text=True, check=True)
    return {"repository": str(repository), "before": before, "after": after, "patch": source.stdout}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repository", type=Path)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(diff_pair(args.repository, args.before, args.after), indent=2),
                           encoding="utf-8")


if __name__ == "__main__":
    main()
