import logging
import re
from collections import Counter
from dataclasses import asdict
from uuid import uuid4

import chromadb

from models import ChunkMetadata, RetrievedChunk

logger = logging.getLogger(__name__)


def collection_name_for(
    base: str,
    provider: str,
    model: str,
    chunking: str,
) -> str:
    """Name a collection after its embedding model and chunking strategy,
    so chunks from different models or strategies never end up in the same
    collection."""

    suffix = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "-",
        f"{provider}__{model}__{chunking}",
    )

    return f"{base}__{suffix.strip('-.')}"


class VectorStore:
    """Stores and retrieves document embeddings using ChromaDB."""

    def __init__(
        self,
        path: str = "./data/chroma",
        collection_name: str = "documents",
        embedding_model: str | None = None,
    ) -> None:
        self.client = chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=(
                {"embedding_model": embedding_model}
                if embedding_model
                else None
            ),
        )

        # Chroma keeps the metadata of an existing collection, so a
        # collection filled by another embedding model has to be caught here.
        stored_model = (self.collection.metadata or {}).get("embedding_model")

        if embedding_model and stored_model and stored_model != embedding_model:
            raise ValueError(
                f"Collection '{collection_name}' holds embeddings from "
                f"'{stored_model}', but the configured embedding model is "
                f"'{embedding_model}'. Upload the documents again or change "
                "the embedding settings."
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
                vector_score=distance,
            )
            for document, metadata, distance in zip(
                documents,
                metadatas,
                distances,
            )
        ]

    def delete_source(self, source: str) -> int:
        """Delete every chunk of a document and return how many were deleted."""

        result = self.collection.get(where={"source": source}, include=[])
        ids = result["ids"]

        if ids:
            logger.info("Deleting %d chunks of %s", len(ids), source)
            self.collection.delete(ids=ids)

        return len(ids)

    def list_sources(self) -> dict[str, int]:
        """Indexed documents and their number of chunks."""

        result = self.collection.get(include=["metadatas"])

        return dict(
            Counter(
                metadata["source"]
                for metadata in result["metadatas"] or []
            )
        )

    def get_all_chunks(self) -> tuple[list[str], list[ChunkMetadata]]:
        result = self.collection.get(include=["documents", "metadatas"])
        documents = result["documents"] or []
        metadatas = [
            ChunkMetadata(**metadata)
            for metadata in result["metadatas"] or []
        ]

        return documents, metadatas