from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ModelResponse:
    patch: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0


class Model(Protocol):
    model_id: str

    def propose(self, prompt: str) -> ModelResponse: ...


class NoOpModel:
    model_id = "none"

    def propose(self, prompt: str) -> ModelResponse:
        return ModelResponse("", self.model_id)


class CommandModel:
    """Local model adapter that reads a prompt on stdin and emits a patch on stdout."""

    def __init__(self, command: list[str], model_id: str = "local-command", timeout: int = 120) -> None:
        if not command:
            raise ValueError("Model command must not be empty")
        self.command = command
        self.model_id = model_id
        self.timeout = timeout

    def propose(self, prompt: str) -> ModelResponse:
        result = subprocess.run(self.command, input=prompt, capture_output=True, text=True,
                                timeout=self.timeout, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Local model command failed")
        return ModelResponse(result.stdout.strip(), self.model_id)
