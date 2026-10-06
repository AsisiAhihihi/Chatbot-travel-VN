"""Small data structures shared by the RAG pipeline."""

from dataclasses import dataclass, field

@dataclass(frozen=True)
class SearchResult:
    text: str
    source: str
    score: float
    index: int
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    sources: list[SearchResult]
    place_ids: list[str] = field(default_factory=list)
    itinerary_ids: list[str] = field(default_factory=list)