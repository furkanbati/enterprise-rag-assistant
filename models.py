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


@dataclass
class RetrievedChunk:
    document: str
    metadata: ChunkMetadata
    distance: float
    vector_score: float | None = None
    keyword_score: float | None = None
    fusion_score: float | None = None


@dataclass
class PipelineResult:
    answer: str
    chunks: list[RetrievedChunk]

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
    page: int
    chunk: int
    heading: str

    vector_score: float | None = None
    keyword_score: float | None = None
    fusion_score: float | None = None
    distance: float
    
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]