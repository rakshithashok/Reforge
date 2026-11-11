from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def split(records: list[dict], seed: int = 17) -> dict[str, list[dict]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    n = len(shuffled)
    train_end, valid_end = int(n * .8), int(n * .9)
    return {"train": shuffled[:train_end], "validation": shuffled[train_end:valid_end],
            "test": shuffled[valid_end:]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    args.output.write_text(json.dumps(split(json.loads(args.input.read_text()), args.seed), indent=2),
                           encoding="utf-8")


if __name__ == "__main__":
    main()
