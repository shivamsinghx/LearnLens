"""Test doubles for heavy dependencies."""

from __future__ import annotations

import hashlib
import math
from typing import Sequence


class FakeEmbeddingBackend:
    """Deterministic, normalized fake encoder — no model download required."""

    def __init__(
        self,
        *,
        model_name: str = "fake/bge-small-en-v1.5",
        dimension: int = 384,
    ) -> None:
        self._model_name = model_name
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(
        self,
        texts: Sequence[str],
        *,
        normalize_embeddings: bool = True,
    ) -> list[list[float]]:
        return [self._vector_for(text, normalize=normalize_embeddings) for text in texts]

    def _vector_for(self, text: str, *, normalize: bool) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        # Expand digest into a stable pseudo-random unit vector.
        seed = list(digest)
        for index in range(self._dimension):
            byte = seed[index % len(seed)]
            mix = (byte + 31 * index + len(text)) % 256
            values.append((mix / 127.5) - 1.0)

        if not normalize:
            return values

        norm = math.sqrt(sum(value * value for value in values))
        if norm == 0:
            values[0] = 1.0
            return values
        return [value / norm for value in values]
