
from generator import Generator
from models import ChunkMetadata, RetrievedChunk


class FakeChatClient:
    def __init__(self, reply="Python is a programming language."):
        self.reply = reply
        self.calls = []

    def complete(self, system, user):
        self.calls.append({"system": system, "user": user})
        return self.reply

    def stream(self, system, user):
        self.calls.append({"system": system, "user": user})
        yield from self.reply.split(" ")


def make_chunk(document):
    return RetrievedChunk(
        document=document,
        metadata=ChunkMetadata(
            source="guide.pdf",
            page=1,
            chunk=0,
            heading="Introduction",
            level=1,
        ),
    )


def test_generate_sends_system_prompt_and_context_to_model():
    client = FakeChatClient()
    generator = Generator(client=client)

    answer = generator.generate(
        question="What is Python?",
        chunks=[make_chunk("Python is a programming language.")],
    )

    assert answer == "Python is a programming language."
    assert len(client.calls) == 1

    call = client.calls[0]
    assert "ONLY the provided context" in call["system"]
    assert "Python is a programming language." in call["user"]
    assert "What is Python?" in call["user"]


def test_build_prompt_includes_all_chunks_and_question():
    generator = Generator(client=FakeChatClient())

    prompt = generator._build_prompt(
        question="What are the features?",
        chunks=[
            make_chunk("Feature one."),
            make_chunk("Feature two."),
        ],
    )

    assert "Context:\n" in prompt
    assert "Feature one." in prompt
    assert "Feature two." in prompt
    assert "Question:\nWhat are the features?" in prompt
    assert prompt.endswith("Answer:")


def test_build_prompt_handles_empty_chunks():
    generator = Generator(client=FakeChatClient())

    prompt = generator._build_prompt(
        question="Unknown question",
        chunks=[],
    )

    assert "Context:\n\n" in prompt
    assert "Unknown question" in prompt
    assert prompt.endswith("Answer:")


def test_stream_uses_the_same_prompt_as_generate():
    client = FakeChatClient(reply="Python is great")
    generator = Generator(client=client)
    chunks = [make_chunk("Python is a programming language.")]

    generator.generate(question="What is Python?", chunks=chunks)
    pieces = list(generator.stream(question="What is Python?", chunks=chunks))

    assert pieces == ["Python", "is", "great"]
    assert client.calls[0] == client.calls[1]


def test_build_prompt_numbers_passages_with_their_source():
    generator = Generator(client=FakeChatClient())

    prompt = generator._build_prompt(
        question="What are the features?",
        chunks=[make_chunk("Feature one."), make_chunk("Feature two.")],
    )

    assert "[1] guide.pdf, page 1\nFeature one." in prompt
    assert "[2] guide.pdf, page 1\nFeature two." in prompt


def test_system_prompt_asks_for_numbered_citations():
    assert "square brackets" in Generator.SYSTEM_PROMPT
    assert "Only cite numbers that appear in" in Generator.SYSTEM_PROMPT
