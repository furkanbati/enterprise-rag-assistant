
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
        language="en",
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


def test_pipeline_retrieves_and_streams_separately():
    embedder = Mock()
    embedder.embed.return_value = [0.1]

    chunk = Mock()
    retriever = Mock()
    retriever.search.return_value = [chunk]

    generator = Mock()
    generator.stream.return_value = iter(["An", "swer"])

    pipeline = Pipeline(
        embedder=embedder,
        retriever=retriever,
        generator=generator,
    )

    chunks = pipeline.retrieve("Q?")
    pieces = list(pipeline.stream("Q?", chunks))

    assert chunks == [chunk]
    assert pieces == ["An", "swer"]
    retriever.search.assert_called_once_with(
        query="Q?", embedding=[0.1], language="en",
    )
    generator.stream.assert_called_once_with(question="Q?", chunks=[chunk])
    generator.generate.assert_not_called()


def make_routed_pipeline():
    embedder = Mock()
    embedder.embed.return_value = [0.1]
    retriever = Mock()
    retriever.search.return_value = []
    default, turkish = Mock(), Mock()
    default.generate.return_value = "default"
    turkish.generate.return_value = "turkish"

    pipeline = Pipeline(
        embedder=embedder,
        retriever=retriever,
        generator=default,
        language_generators={"tr": turkish},
    )

    return pipeline, retriever, default, turkish


def test_pipeline_routes_turkish_questions_to_the_turkish_generator():
    pipeline, retriever, default, turkish = make_routed_pipeline()

    assert pipeline.run("Veri sorumlusu kimdir?").answer == "turkish"
    assert retriever.search.call_args.kwargs["language"] == "tr"
    default.generate.assert_not_called()


def test_pipeline_keeps_english_questions_on_the_default_generator():
    pipeline, retriever, default, turkish = make_routed_pipeline()

    assert pipeline.run("What is GOVERN?").answer == "default"
    assert retriever.search.call_args.kwargs["language"] == "en"
    turkish.generate.assert_not_called()


def test_pipeline_streams_with_the_generator_of_the_question_language():
    pipeline, _, default, turkish = make_routed_pipeline()
    turkish.stream.return_value = iter(["Türkçe"])

    assert list(pipeline.stream("Kurul kaç üyeden oluşur?", [])) == ["Türkçe"]
    default.stream.assert_not_called()


def test_pipeline_without_language_generators_uses_the_default_for_all():
    generator = Mock()
    pipeline = Pipeline(embedder=Mock(), retriever=Mock(), generator=generator)

    assert pipeline.generator_for("tr") is generator
    assert pipeline.generator_for("en") is generator
