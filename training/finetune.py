"""Fine-tune a causal language model on migration patches with LoRA."""

from __future__ import annotations

import argparse
from pathlib import Path


def _format(record: dict[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Dataset record is missing non-empty {field!r}")
    return value


def train(dataset_path: str, base_model: str, output: Path, text_field: str = "patch",
          max_length: int = 1024, epochs: float = 1.0, batch_size: int = 1,
          learning_rate: float = 2e-4) -> None:
    """Run a compact causal-LM LoRA recipe and save adapter weights and tokenizer."""
    try:
        from datasets import load_dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise RuntimeError("Install reforge-migrations[training] to fine-tune a model") from exc

    dataset = load_dataset("json", data_files=dataset_path, split="train")
    if not len(dataset):
        raise ValueError("Training dataset is empty")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def tokenize(record: dict[str, object]) -> dict[str, object]:
        encoded = tokenizer(_format(record, text_field), truncation=True, max_length=max_length)
        encoded["labels"] = list(encoded["input_ids"])
        return encoded

    tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)
    model = AutoModelForCausalLM.from_pretrained(base_model)
    model.config.pad_token_id = tokenizer.pad_token_id
    model = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM, r=16,
                                              lora_alpha=32, lora_dropout=0.05))
    arguments = TrainingArguments(
        output_dir=str(output),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        save_strategy="epoch",
        logging_steps=10,
        report_to=[],
    )
    trainer = Trainer(model=model, args=arguments, train_dataset=tokenized,
                      data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False))
    trainer.train()
    output.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output))
    tokenizer.save_pretrained(str(output))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="JSONL file containing migration patches")
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--text-field", default="patch")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    args = parser.parse_args()
    train(args.dataset, args.base_model, args.output, args.text_field, args.max_length,
          args.epochs, args.batch_size, args.learning_rate)


if __name__ == "__main__":
    main()
