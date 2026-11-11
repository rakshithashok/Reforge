from __future__ import annotations

from reforge.models.base import Model


def repair_loop(model: Model, prompt: str, max_iterations: int = 3) -> list[str]:
    """Generate bounded candidate patches; applying and verifying is pipeline-owned."""
    proposals: list[str] = []
    seen: set[str] = set()
    for _ in range(max_iterations):
        response = model.propose(prompt)
        if not response.patch or response.patch in seen:
            break
        proposals.append(response.patch)
        seen.add(response.patch)
        prompt += "\n\nPrevious patch failed. Produce a different minimal patch."
    return proposals
