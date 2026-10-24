from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Page:
    number: int
    text: str


@dataclass
class ChunkMetadata:
    source: str
    page: int
    chunk: int
    heading: str
    level: int
    # Document title; empty for chunks indexed before titles were stored.
    title: str = ""


@dataclass
class RetrievedChunk:
    document: str
    metadata: ChunkMetadata
    vector_score: float | None = None
    keyword_score: float | None = None
    fusion_score: float | None = None
    rerank_score: float | None = None

@dataclass
class PipelineResult:
    answer: str
    chunks: list[RetrievedChunk]

@dataclass
class IngestionResult:
    source: str
    chunks: int
    replaced: bool

@dataclass
class Section:
    heading: str
    level: int
    page: int
    text: str

# ----------------------------
# API Response Models
# ----------------------------

class SourceResponse(BaseModel):
    source: str
    title: str = ""
    page: int
    chunk: int
    heading: str
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]