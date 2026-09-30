"""
ingest.py — PDF Ingestion Pipeline
====================================
This script reads a PDF from the documents/ folder, extracts text page-by-page,
splits it into overlapping chunks, creates embeddings via Hugging Face API,
and stores everything in Qdrant Cloud.

Run:  python ingest.py
"""

import os
import sys
import uuid

# Fix Windows console encoding for emojis/unicode
sys.stdout.reconfigure(encoding='utf-8')

import pymupdf  # PyMuPDF (formerly 'fitz')
import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# ─── Configuration ──────────────────────────────────────────────────────────────

PDF_PATH = os.path.join("documents", "university_rules.pdf")
COLLECTION_NAME = "university_docs"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between consecutive chunks

# ─── Load Environment Variables ─────────────────────────────────────────────────

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def check_environment():
    """Make sure all required env vars and files are present."""
    errors = []

    if not HF_TOKEN:
        errors.append("❌ HF_TOKEN is missing. Add it to your .env file.")
    if not QDRANT_URL:
        errors.append("❌ QDRANT_URL is missing. Add it to your .env file.")
    if not QDRANT_API_KEY:
        errors.append("❌ QDRANT_API_KEY is missing. Add it to your .env file.")
    if not os.path.exists(PDF_PATH):
        errors.append(f"❌ PDF file not found at: {PDF_PATH}")

    if errors:
        for e in errors:
            print(e)
        sys.exit(1)

    print("✅ Environment variables loaded successfully.")
    print(f"   PDF path       : {PDF_PATH}")
    print(f"   Qdrant URL     : {QDRANT_URL}")
    print(f"   Embedding model: {EMBEDDING_MODEL}")


# ─── PDF Text Extraction ────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Opens the PDF and extracts text page-by-page.
    Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
    """
    print(f"\n📄 Opening PDF: {pdf_path}")
    doc = pymupdf.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append({
                "page": page_num + 1,   # 1-indexed
                "text": text.strip()
            })

    doc.close()

    if not pages:
        print("❌ The PDF has no extractable text. Make sure it is not a scanned image PDF.")
        sys.exit(1)

    print(f"   ✅ Extracted text from {len(pages)} page(s).")
    return pages


# ─── Chunking ───────────────────────────────────────────────────────────────────

def split_into_chunks(pages: list[dict], chunk_size: int = CHUNK_SIZE,
                      chunk_overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """
    Takes page-level text and splits it into smaller overlapping chunks.
    Each chunk keeps track of its source page number and filename.
    """
    chunks = []
    source_filename = os.path.basename(PDF_PATH)

    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "page": page_num,
                    "source": source_filename
                })

            start += chunk_size - chunk_overlap

    print(f"   ✅ Created {len(chunks)} text chunk(s)  "
          f"(size={chunk_size}, overlap={chunk_overlap}).")
    return chunks


# ─── Embedding Generation ───────────────────────────────────────────────────────

def create_embeddings(chunks: list[dict], hf_client: InferenceClient) -> list[list[float]]:
    """
    Sends each chunk's text to the Hugging Face hosted embedding model
    and returns a list of embedding vectors.
    """
    print(f"\n🔢 Generating embeddings using: {EMBEDDING_MODEL}")
    embeddings = []

    for i, chunk in enumerate(chunks):
        # feature_extraction returns a list (or nested list) of floats
        result = hf_client.feature_extraction(
            text=chunk["text"],
            model=EMBEDDING_MODEL
        )

        # Convert to a flat numpy array then to a plain list
        vec = np.array(result, dtype=np.float32)

        # If shape is (1, seq_len, dim) or (seq_len, dim), mean-pool to (dim,)
        if vec.ndim == 3:
            vec = vec.mean(axis=1).squeeze()
        elif vec.ndim == 2:
            vec = vec.mean(axis=0)

        embeddings.append(vec.tolist())

        if (i + 1) % 10 == 0 or (i + 1) == len(chunks):
            print(f"   ... embedded {i + 1}/{len(chunks)} chunks")

    print(f"   ✅ All {len(embeddings)} embeddings generated.")
    return embeddings


# ─── Qdrant Cloud Storage ───────────────────────────────────────────────────────

def store_in_qdrant(chunks: list[dict], embeddings: list[list[float]]):
    """
    Connects to Qdrant Cloud, creates (or recreates) the collection,
    and upserts all chunk vectors with their metadata.
    """
    # Determine vector dimension from the first embedding
    vector_dim = len(embeddings[0])
    print(f"\n☁️  Connecting to Qdrant Cloud ...")
    print(f"   Vector dimension: {vector_dim}")

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )

    # Recreate collection (start fresh each time)
    print(f"   Creating collection: '{COLLECTION_NAME}' ...")
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_dim,
            distance=Distance.COSINE
        )
    )
    print(f"   ✅ Collection '{COLLECTION_NAME}' created with cosine similarity.")

    # Build point objects
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "page": chunk["page"],
                    "source": chunk["source"]
                }
            )
        )

    # Upsert in a single batch
    print(f"   Uploading {len(points)} vectors ...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"   ✅ All vectors stored in Qdrant Cloud successfully!")

    return client


# ─── Test Search ─────────────────────────────────────────────────────────────────

def test_search(client: QdrantClient, hf_client: InferenceClient):
    """
    Runs a quick test search to make sure everything is working.
    """
    test_query = "What are the rules for students?"
    print(f"\n🔍 Running test search: \"{test_query}\"")

    # Create query embedding
    result = hf_client.feature_extraction(
        text=test_query,
        model=EMBEDDING_MODEL
    )
    vec = np.array(result, dtype=np.float32)
    if vec.ndim == 3:
        vec = vec.mean(axis=1).squeeze()
    elif vec.ndim == 2:
        vec = vec.mean(axis=0)
    query_vector = vec.tolist()

    # Search
    search_response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=3
    )

    print(f"\n📋 Top 3 results:\n")
    for i, hit in enumerate(search_response.points, 1):
        payload = hit.payload
        score = hit.score
        print(f"   Result {i}  (score: {score:.4f})")
        print(f"   Page  : {payload['page']}")
        print(f"   Source: {payload['source']}")
        print(f"   Text  : {payload['text'][:200]}...")
        print()


# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("   RAG PDF Chatbot — Ingestion Pipeline")
    print("=" * 60)

    # Step 1: Check environment
    check_environment()

    # Step 2: Create Hugging Face client
    hf_client = InferenceClient(token=HF_TOKEN)

    # Step 3: Extract text from PDF
    pages = extract_text_from_pdf(PDF_PATH)

    # Step 4: Split into chunks
    chunks = split_into_chunks(pages)

    # Step 5: Generate embeddings
    embeddings = create_embeddings(chunks, hf_client)

    # Step 6: Store in Qdrant Cloud
    qdrant_client = store_in_qdrant(chunks, embeddings)

    # Step 7: Test search
    test_search(qdrant_client, hf_client)

    print("=" * 60)
    print("   ✅ Ingestion complete! You can now run: python rag.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
