
from types import SimpleNamespace
from unittest.mock import Mock

from providers.openai import OpenAIChatClient, OpenAIEmbedder


def make_chat_client(content="GOVERN is cross-cutting."):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )
    return client


def embedding_response(vectors, order=None):
    order = order or range(len(vectors))
    return SimpleNamespace(
        data=[
            SimpleNamespace(index=i, embedding=vectors[i])
            for i in order
        ]
    )


def test_chat_client_sends_model_messages_and_reasoning_effort():
    client = make_chat_client()
    chat = OpenAIChatClient(
        client=client,
        model="gpt-test",
        reasoning_effort="low",
    )

    reply = chat.complete(system="System prompt.", user="Question?")

    assert reply == "GOVERN is cross-cutting."
    client.chat.completions.create.assert_called_once_with(
        model="gpt-test",
        messages=[
            {"role": "system", "content": "System prompt."},
            {"role": "user", "content": "Question?"},
        ],
        reasoning_effort="low",
    )


def test_chat_client_omits_reasoning_effort_when_not_set():
    client = make_chat_client()
    chat = OpenAIChatClient(client=client, model="gpt-test")

    chat.complete(system="System prompt.", user="Question?")

    call = client.chat.completions.create.call_args.kwargs
    assert "reasoning_effort" not in call


def test_chat_client_returns_empty_string_for_missing_content():
    chat = OpenAIChatClient(
        client=make_chat_client(content=None),
        model="gpt-test",
    )

    assert chat.complete(system="System prompt.", user="Question?") == ""


def test_embedder_embeds_single_text():
    client = Mock()
    client.embeddings.create.return_value = embedding_response([[0.1, 0.2]])
    embedder = OpenAIEmbedder(client=client, model="embed-test")

    assert embedder.embed("hello") == [0.1, 0.2]
    client.embeddings.create.assert_called_once_with(
        model="embed-test",
        input=["hello"],
    )


def test_embedder_orders_results_by_index():
    client = Mock()
    client.embeddings.create.return_value = embedding_response(
        [[0.0], [1.0], [2.0]],
        order=[2, 0, 1],
    )
    embedder = OpenAIEmbedder(client=client, model="embed-test")

    assert embedder.embed_batch(["a", "b", "c"]) == [[0.0], [1.0], [2.0]]


def test_embedder_splits_large_batches():
    client = Mock()
    client.embeddings.create.side_effect = (
        lambda model, input: embedding_response(
            [[float(len(text))] for text in input]
        )
    )
    embedder = OpenAIEmbedder(client=client, model="embed-test")
    texts = ["x" * (i % 5 + 1) for i in range(300)]

    embeddings = embedder.embed_batch(texts)

    batch_sizes = [
        len(call.kwargs["input"])
        for call in client.embeddings.create.call_args_list
    ]
    assert batch_sizes == [256, 44]
    assert embeddings == [[float(len(text))] for text in texts]


def test_embedder_handles_empty_batch():
    client = Mock()
    embedder = OpenAIEmbedder(client=client, model="embed-test")

    assert embedder.embed_batch([]) == []
    client.embeddings.create.assert_not_called()


def stream_chunk(content=None, has_choice=True):
    choices = [SimpleNamespace(delta=SimpleNamespace(content=content))] if has_choice else []
    return SimpleNamespace(choices=choices)


def test_chat_client_streams_deltas_and_skips_empty_chunks():
    client = Mock()
    client.chat.completions.create.return_value = iter([
        stream_chunk("GOVERN "),
        stream_chunk(None),
        stream_chunk("is cross-cutting."),
        stream_chunk(has_choice=False),
    ])
    chat = OpenAIChatClient(client=client, model="gpt-test", reasoning_effort="low")

    pieces = list(chat.stream(system="System prompt.", user="Question?"))

    assert pieces == ["GOVERN ", "is cross-cutting."]
    call = client.chat.completions.create.call_args.kwargs
    assert call["stream"] is True
    assert call["reasoning_effort"] == "low"
    assert call["model"] == "gpt-test"
