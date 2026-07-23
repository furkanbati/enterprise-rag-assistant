import logging
from dataclasses import asdict
from uuid import uuid4

import chromadb

from models import ChunkMetadata, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStore:
    """Stores and retrieves document embeddings using ChromaDB."""

    def __init__(
        self,
        path: str = "./data/chroma",
        collection_name: str = "documents",
    ) -> None:
        self.client = chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
        )

    def add(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[ChunkMetadata],
    ) -> None:
        logger.info("Adding %d document chunks to vector store", len(documents))

        ids = [
            str(uuid4())
            for _ in documents
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=[
                asdict(metadata)
                for metadata in metadatas
            ],
        )

    def query(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        logger.info(
            "Retrieving top %d document chunks from vector store",
            top_k,
        )

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            RetrievedChunk(
                document=document,
                metadata=ChunkMetadata(**metadata),
                distance=distance,
            )
            for document, metadata, distance in zip(
                documents,
                metadatas,
                distances,
            )
        ]