"""Streamlit chat interface for the RAG API.

Run with `streamlit run ui/app.py`; set API_URL to point at the API.
"""

import os

import streamlit as st

from client import ApiClient, ApiError

API_URL = os.getenv("API_URL", "http://localhost:8000")

UPLOAD_TYPES = ["pdf", "docx", "html", "htm", "md", "txt"]

api = ApiClient(API_URL)

st.set_page_config(
    page_title="Enterprise RAG Assistant",
    page_icon="📄",
    layout="wide",
)


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"Sources ({len(sources)})"):
        for source in sources:
            # Older indexes have no document titles; fall back to the file name.
            name = source.get("title") or source["source"]
            title = f"**{name}** · page {source['page']}"

            if source["heading"] and source["heading"] != name:
                title += f" · {source['heading']}"

            st.markdown(title)

            if source.get("title"):
                st.caption(source["source"])

            st.caption(source["preview"])


def render_timing(timing: dict | None) -> None:
    if timing:
        st.caption(
            f"Retrieval {timing['retrieval_ms'] / 1000:.1f} s · "
            f"Generation {timing['generation_ms'] / 1000:.1f} s"
        )


def render_document(document: dict) -> None:
    """One row of the document list, with a confirmed remove action."""

    name_column, remove_column = st.columns([3, 1], vertical_alignment="center")
    name_column.markdown(
        f"{document['source']}  \n:gray[{document['chunks']} chunks]"
    )

    with remove_column.popover(":material/delete:", help="Remove document"):
        st.write(f"Remove **{document['source']}** from the index?")

        if st.button("Remove", key=f"remove-{document['source']}", type="primary"):
            try:
                api.delete_document(document["source"])
            except ApiError as e:
                st.error(str(e))
            else:
                st.session_state["notice"] = f"Removed {document['source']}."
                st.rerun()


def render_sidebar() -> None:
    st.header("Enterprise RAG Assistant")

    try:
        info = api.info()
    except ApiError as e:
        st.error(str(e))
        st.stop()

    st.subheader("Configuration")
    st.markdown(
        f"- **Chat model:** `{info['chat_model']}`\n"
        f"- **Embeddings:** `{info['embedding_model']}`\n"
        f"- **Chunking:** `{info['chunking']}`\n"
        f"- **Reranker:** `{info['reranker']}`"
    )

    st.subheader("Documents")

    if info["documents"]:
        for document in info["documents"]:
            render_document(document)
    else:
        st.info("No documents indexed yet. Upload a document to start.")

    # Shown once after the rerun that refreshes the document list.
    if notice := st.session_state.pop("notice", None):
        st.success(notice)

    uploaded = st.file_uploader(
        "Add a document",
        type=UPLOAD_TYPES,
        help="Uploading a file with the name of an indexed document replaces it.",
    )

    if uploaded and st.button("Index document", use_container_width=True):
        with st.spinner(f"Indexing {uploaded.name}..."):
            try:
                result = api.upload(uploaded.name, uploaded.getvalue())
            except ApiError as e:
                st.error(str(e))
            else:
                verb = "Replaced" if result["replaced"] else "Indexed"
                st.session_state["notice"] = (
                    f"{verb} {result['source']} ({result['chunks']} chunks)."
                )
                st.rerun()

    st.divider()
    st.caption(
        "Each question is answered on its own: earlier messages are not "
        "sent to the model."
    )


def answer(question: str) -> dict:
    """Stream the answer to a question into the page and return it as a
    message for the history."""

    result = {"sources": [], "timing": None, "error": None}
    status = st.empty()
    status.caption("Searching the documents...")

    def tokens():
        for event in api.stream_answer(question):
            if event["type"] == "sources":
                result["sources"] = event["sources"]
                status.caption(
                    f"Found {len(event['sources'])} sources, generating the answer..."
                )
            elif event["type"] == "token":
                status.empty()
                yield event["text"]
            elif event["type"] == "done":
                result["timing"] = event
            elif event["type"] == "error":
                result["error"] = event["detail"]

    try:
        content = st.write_stream(tokens())
    except ApiError as e:
        content = ""
        result["error"] = str(e)

    status.empty()

    if result["error"]:
        st.error(result["error"])

    render_sources(result["sources"])
    render_timing(result["timing"])

    return {
        "role": "assistant",
        "content": content or "",
        **result,
    }


with st.sidebar:
    render_sidebar()

st.title("Ask your documents")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            if message.get("error"):
                st.error(message["error"])

            render_sources(message.get("sources", []))
            render_timing(message.get("timing"))

if question := st.chat_input("Ask a question about the indexed documents"):
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        st.session_state.messages.append(answer(question))
