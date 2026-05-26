from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """Retrievable document chunk. Shape mirrors a SharePoint document or
    Dataverse table row — the kind of low-code-platform-native record Power
    Platform connects to natively."""

    chunk_id: str
    source_type: str  # spec | indications | surgical_technique | case | compliance
    source_id: str
    section: str | None
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float
    matched_terms: list[str] = field(default_factory=list)
