"""
rag.py — RAG (Retrieval-Augmented Generation) Pipeline
=======================================================
This module:
  1. Takes a user question
  2. Creates a query embedding via Hugging Face API
  3. Searches Qdrant Cloud for relevant chunks
  4. Sends the retrieved context + question to Qwen LLM
  5. Returns an answer grounded in the PDF content

Run interactively:  python rag.py
"""

import os
import sys

# Fix Windows console encoding for emojis/unicode
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient

# ─── Configuration ──────────────────────────────────────────────────────────────

COLLECTION_NAME = "university_docs"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "Qwen/Qwen2.5-72B-Instruct"
TOP_K = 5  # number of relevant chunks to retrieve

SYSTEM_PROMPT = """You are a university document assistant.
Answer the user's question using ONLY the provided document context below.
Do not invent or assume any information that is not in the context.
If the answer is not available in the context, clearly say:
"Sorry, I could not find this information in the provided document."
When possible, mention the relevant page number(s) in your answer."""

# ─── Load Environment Variables ─────────────────────────────────────────────────

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def check_environment():
    """Verify all env vars are present."""
    errors = []
    if not HF_TOKEN:
        errors.append("❌ HF_TOKEN missing in .env")
    if not QDRANT_URL:
        errors.append("❌ QDRANT_URL missing in .env")
    if not QDRANT_API_KEY:
        errors.append("❌ QDRANT_API_KEY missing in .env")
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)


# ─── Clients (initialized once, reused across calls) ────────────────────────────

check_environment()

hf_client = InferenceClient(token=HF_TOKEN)

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


# ─── Helper: Create Query Embedding ─────────────────────────────────────────────

def get_query_embedding(query: str) -> list[float]:
    """
    Converts the user's question into an embedding vector
    using the Hugging Face hosted embedding model.
    """
    result = hf_client.feature_extraction(
        text=query,
        model=EMBEDDING_MODEL
    )

    vec = np.array(result, dtype=np.float32)

    # Mean-pool if needed (same logic as ingest.py)
    if vec.ndim == 3:
        vec = vec.mean(axis=1).squeeze()
    elif vec.ndim == 2:
        vec = vec.mean(axis=0)

    return vec.tolist()


# ─── Helper: Search Qdrant ───────────────────────────────────────────────────────

def search_qdrant(query_vector: list[float], top_k: int = TOP_K) -> list[dict]:
    """
    Searches Qdrant Cloud for the most relevant document chunks.
    Returns a list of dicts with text, page, source, and score.
    """
    response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )

    retrieved = []
    for hit in response.points:
        retrieved.append({
            "text": hit.payload["text"],
            "page": hit.payload["page"],
            "source": hit.payload["source"],
            "score": round(hit.score, 4)
        })

    return retrieved


# ─── Helper: Build Context String ────────────────────────────────────────────────

def build_context(retrieved_chunks: list[dict]) -> str:
    """
    Combines the retrieved chunks into a single context string
    that will be sent to the LLM.
    """
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"[Chunk {i} | Page {chunk['page']} | {chunk['source']}]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(context_parts)


# ─── Helper: Format Sources ─────────────────────────────────────────────────────

def format_sources(retrieved_chunks: list[dict]) -> str:
    """
    Creates a human-readable summary of the source chunks used.
    """
    lines = ["📚 Sources used:"]
    seen = set()
    for chunk in retrieved_chunks:
        key = (chunk["page"], chunk["source"])
        if key not in seen:
            seen.add(key)
            lines.append(f"   • Page {chunk['page']}  ({chunk['source']})  "
                         f"— relevance: {chunk['score']}")
    return "\n".join(lines)


# ─── Main RAG Function ──────────────────────────────────────────────────────────

def ask_question(question: str) -> dict:
    """
    End-to-end RAG pipeline.

    Args:
        question: The user's natural-language question.

    Returns:
        dict with keys:
            "answer"  — the LLM-generated answer
            "sources" — formatted source information string
            "chunks"  — raw list of retrieved chunk dicts
    """
    # Step 1: Create query embedding
    query_vector = get_query_embedding(question)

    # Step 2: Search Qdrant for relevant chunks
    retrieved_chunks = search_qdrant(query_vector)

    if not retrieved_chunks:
        return {
            "answer": "Sorry, I could not find any relevant information in the document.",
            "sources": "No sources found.",
            "chunks": []
        }

    # Step 3: Build context from retrieved chunks
    context = build_context(retrieved_chunks)

    # Step 4: Create the prompt for the LLM
    user_message = (
        f"Document Context:\n"
        f"─────────────────\n"
        f"{context}\n"
        f"─────────────────\n\n"
        f"Question: {question}\n\n"
        f"Answer the question using ONLY the document context above. "
        f"Mention page numbers when relevant."
    )

    # Step 5: Call Qwen LLM via Hugging Face
    try:
        response = hf_client.chat_completion(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1024,
            temperature=0.3
        )

        answer = response.choices[0].message.content.strip()

    except Exception as e:
        answer = f"⚠️ Error calling LLM: {str(e)}"

    # Step 6: Format sources
    sources = format_sources(retrieved_chunks)

    return {
        "answer": answer,
        "sources": sources,
        "chunks": retrieved_chunks
    }


# ─── Interactive Terminal Mode ───────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("   University PDF RAG Chatbot — Terminal Mode")
    print("=" * 60)
    print(f"   Embedding model : {EMBEDDING_MODEL}")
    print(f"   LLM model       : {LLM_MODEL}")
    print(f"   Top K chunks    : {TOP_K}")
    print(f"   Collection      : {COLLECTION_NAME}")
    print("=" * 60)
    print("\nType your question and press Enter.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("❓ You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 👋")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Goodbye! 👋")
            break

        print("\n⏳ Searching and generating answer ...\n")
        result = ask_question(question)

        print(f"🤖 Answer:\n{result['answer']}\n")
        print(f"{result['sources']}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
