"""Chunk-level diff utility for incremental ingestion."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from backend.app.shared.models.models import Chunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkDiff:
    unchanged: list[Chunk] = field(default_factory=list)
    updated: list[Chunk] = field(default_factory=list)
    inserted: list[Chunk] = field(default_factory=list)
    removed: list[Chunk] = field(default_factory=list)


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assign_chunk_hashes(chunks: list[Chunk]) -> None:
    for chunk in chunks:
        chunk.content_hash = compute_content_hash(chunk.text)


def diff_chunks(old_chunks: list[Chunk], new_chunks: list[Chunk]) -> ChunkDiff:
    # Compare old and new chunk lists and return a ChunkDiff.

    old_by_index: dict[int, Chunk] = {c.chunk_index: c for c in old_chunks}
    new_by_index: dict[int, Chunk] = {c.chunk_index: c for c in new_chunks}

    diff = ChunkDiff()

    old_indices = set(old_by_index.keys())
    new_indices = set(new_by_index.keys())

    common_indices = old_indices & new_indices
    removed_indices = old_indices - new_indices
    inserted_indices = new_indices - old_indices

    for idx in sorted(common_indices):
        old = old_by_index[idx]
        new = new_by_index[idx]
        if old.content_hash == new.content_hash:
            diff.unchanged.append(old)
        else:
            diff.updated.append(new)

    for idx in sorted(removed_indices):
        diff.removed.append(old_by_index[idx])

    for idx in sorted(inserted_indices):
        diff.inserted.append(new_by_index[idx])

    logger.info(
        "Chunk diff: %d unchanged, %d updated, %d inserted, %d removed.",
        len(diff.unchanged),
        len(diff.updated),
        len(diff.inserted),
        len(diff.removed),
    )

    return diff
