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


@dataclass
class RetrievedChunk:
    document: str
    metadata: ChunkMetadata
    distance: float


@dataclass
class PipelineResult:
    answer: str
    chunks: list[RetrievedChunk]


# ----------------------------
# API Response Models
# ----------------------------

class SourceResponse(BaseModel):
    source: str
    page: int
    chunk: int
    distance: float
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]