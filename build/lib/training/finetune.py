"""LoRA fine-tuning entry point; requires the optional training dependencies."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        import torch  # noqa: F401
        from datasets import load_dataset
        from peft import LoraConfig  # noqa: F401
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: F401
    except ImportError as exc:
        raise SystemExit("Install reforge-migrations[training] to fine-tune a model") from exc
    raise SystemExit("Training recipe selection is intentionally explicit and not yet implemented")


if __name__ == "__main__":
    main()
