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