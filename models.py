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


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]