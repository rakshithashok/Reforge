from __future__ import annotations

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
