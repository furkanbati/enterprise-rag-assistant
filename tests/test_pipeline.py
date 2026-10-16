
from unittest.mock import Mock

from models import PipelineResult
from pipeline import Pipeline


def test_pipeline_embeds_retrieves_and_generates_answer():
    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2, 0.3]

    chunk = Mock()
    retriever = Mock()
    retriever.search.return_value = [chunk]

    generator = Mock()
    generator.generate.return_value = "Answer from context."

    pipeline = Pipeline(
        embedder=embedder,
        retriever=retriever,
        generator=generator,
    )

    result = pipeline.run("What is Python?")

    assert result == PipelineResult(
        answer="Answer from context.",
        chunks=[chunk],
    )

    embedder.embed.assert_called_once_with("What is Python?")
    retriever.search.assert_called_once_with(
        query="What is Python?",
        embedding=[0.1, 0.2, 0.3],
    )
    generator.generate.assert_called_once_with(
        question="What is Python?",
        chunks=[chunk],
    )


def test_pipeline_generates_answer_when_no_chunks_are_found():
    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    retriever = Mock()
    retriever.search.return_value = []

    generator = Mock()
    generator.generate.return_value = "I don't know."

    pipeline = Pipeline(
        embedder=embedder,
        retriever=retriever,
        generator=generator,
    )

    result = pipeline.run("Unknown question")

    assert result.answer == "I don't know."
    assert result.chunks == []
    generator.generate.assert_called_once_with(
        question="Unknown question",
        chunks=[],
    )
