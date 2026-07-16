from dataclasses import dataclass


@dataclass
class Page:
    page: int
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