from uuid import uuid4

import chromadb


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
        )

    def query(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[str]:
        logger.info("Retrieving top %d documents from vector store", top_k)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )

        return results["documents"][0]