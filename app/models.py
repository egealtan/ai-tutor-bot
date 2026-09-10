from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrievedChunk:
    id: int
    filename: str
    page_number: int
    content: str
    score: float


@dataclass
class TutorResult:
    answer: str
    sources: list[RetrievedChunk] = field(default_factory=list)
    fallback: bool = False
