"""The retrieval components the evaluations share, built from config.py the
same way the API builds them."""

from dataclasses import dataclass

from chunking import build_chunker, chunking_id
from config import (
    CHROMA_PATH,
    CHUNK_CONTEXT,
    CHUNKING_STRATEGY,
    COLLECTION_NAME,
    EMBED_MODEL,
    EMBED_PROVIDER,
    MAX_CHUNK_SIZE,
    MIN_CHUNK_SIZE,
    OCR_ENGINE,
    RETRIEVAL_TOP_K,
    SEMANTIC_PERCENTILE,
    SEMANTIC_WINDOW,
)
from evaluation.strategies import (
    HybridRerankStrategy,
    HybridStrategy,
    KeywordOnlyStrategy,
    RetrievalStrategy,
    VectorOnlyStrategy,
)
from ingestion import Ingestion
from providers.base import Embedder
from providers.factory import build_embedder
from retrieval.fusion import ReciprocalRankFusion
from retrieval.keyword_search import KeywordSearch
from retrieval.reranker import CrossEncoderReranker
from retrieval.vector_search import VectorSearch
from vector_store import VectorStore, collection_name_for


@dataclass
class RetrievalComponents:
    chunking: str
    vector_store: VectorStore
    embedder: Embedder
    vector_search: VectorSearch
    keyword_search: KeywordSearch
    fusion: ReciprocalRankFusion


def current_chunking() -> str:
    return chunking_id(
        CHUNKING_STRATEGY,
        SEMANTIC_PERCENTILE,
        SEMANTIC_WINDOW,
        CHUNK_CONTEXT,
    )


def build_components() -> RetrievalComponents:
    """Open the collection the API uses and build the search components."""

    chunking = current_chunking()

    vector_store = VectorStore(
        path=CHROMA_PATH,
        collection_name=collection_name_for(
            COLLECTION_NAME,
            EMBED_PROVIDER,
            EMBED_MODEL,
            chunking,
        ),
        embedding_model=f"{EMBED_PROVIDER}/{EMBED_MODEL}",
    )

    vector_search = VectorSearch(vector_store)
    keyword_search = KeywordSearch(vector_store)
    keyword_search.rebuild()

    return RetrievalComponents(
        chunking=chunking,
        vector_store=vector_store,
        embedder=build_embedder(provider=EMBED_PROVIDER, model=EMBED_MODEL),
        vector_search=vector_search,
        keyword_search=keyword_search,
        fusion=ReciprocalRankFusion(),
    )


def build_strategies(
    components: RetrievalComponents,
    rerank_model: str,
    names: list[str] | None = None,
    rerank_model_tr: str | None = None,
) -> dict[str, RetrievalStrategy]:
    """The retrieval strategies to compare, by name.

    The cross-encoder is only loaded when the reranking strategy is requested.
    Turkish questions are reranked with ``rerank_model_tr`` when it is set
    and differs from ``rerank_model``, as in the API.
    """

    def language_rerankers() -> dict[str, CrossEncoderReranker] | None:
        if rerank_model_tr and rerank_model_tr != rerank_model:
            return {"tr": CrossEncoderReranker(rerank_model_tr)}

        return None

    builders = {
        "vector": lambda: VectorOnlyStrategy(components.vector_search),
        "bm25": lambda: KeywordOnlyStrategy(components.keyword_search),
        "hybrid_rrf": lambda: HybridStrategy(
            vector_search=components.vector_search,
            keyword_search=components.keyword_search,
            fusion=components.fusion,
            candidate_top_k=RETRIEVAL_TOP_K,
        ),
        "hybrid_rrf_rerank": lambda: HybridRerankStrategy(
            vector_search=components.vector_search,
            keyword_search=components.keyword_search,
            fusion=components.fusion,
            reranker=CrossEncoderReranker(rerank_model),
            candidate_top_k=RETRIEVAL_TOP_K,
            language_rerankers=language_rerankers(),
        ),
    }

    if names is None:
        names = list(builders)

    unknown = [name for name in names if name not in builders]

    if unknown:
        raise ValueError(f"Unknown retrieval strategy: {', '.join(unknown)}")

    return {name: builders[name]() for name in names}


def build_ingestion(components: RetrievalComponents) -> Ingestion:
    """Ingestion into the evaluated collection, configured like the API's."""

    return Ingestion(
        embedder=components.embedder,
        vector_store=components.vector_store,
        chunker=build_chunker(
            strategy=CHUNKING_STRATEGY,
            embedder=components.embedder,
            max_chunk_size=MAX_CHUNK_SIZE,
            min_chunk_size=MIN_CHUNK_SIZE,
            breakpoint_percentile=SEMANTIC_PERCENTILE,
            window=SEMANTIC_WINDOW,
            include_title=CHUNK_CONTEXT,
        ),
        keyword_search=components.keyword_search,
        ocr_engine=OCR_ENGINE,
    )
