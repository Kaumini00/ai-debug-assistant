import os
import chromadb
from sentence_transformers import SentenceTransformer

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")

def get_collection(codebase_path: str):
    """Get or create a ChromaDB collection for this codebase."""
    # Use codebase path as collection name
    collection_name = codebase_path.replace("/", "_").replace("\\", "_").replace(":", "").strip("_")
    collection_name = collection_name[-60:]
    return chroma_client.get_or_create_collection(name=collection_name)

def chunk_code(content: str, chunk_size: int = 30) -> list:
    """Split code into chunks of N lines."""
    lines = content.splitlines()
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i:i + chunk_size])
        if chunk.strip():  # skip empty chunks
            chunks.append({
                "text": chunk,
                "start_line": i + 1,
                "end_line": min(i + chunk_size, len(lines))
            })
    return chunks

def index_codebase(codebase_path: str) -> int:
    """
    Walk the codebase, chunk all .py files,
    embed them and store in ChromaDB.
    Returns number of chunks indexed.
    """
    collection = get_collection(codebase_path)

    # Clear existing data
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"[Indexer] Cleared {len(existing['ids'])} existing chunks")

    all_chunks = []
    all_embeddings = []
    all_ids = []
    all_metadata = []

    chunk_id = 0

    for root, _, files in os.walk(codebase_path):
        # Skip hidden folders and virtual environments
        if any(skip in root for skip in [".venv", "__pycache__", ".git", "node_modules"]):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", errors="ignore") as f:
                    content = f.read()
            except Exception as e:
                print(f"[Indexer] Could not read {file_path}: {e}")
                continue

            chunks = chunk_code(content)

            for chunk in chunks:
                all_chunks.append(chunk["text"])
                all_ids.append(f"chunk_{chunk_id}")
                all_metadata.append({
                    "file": file_path,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"]
                })
                chunk_id += 1

    if not all_chunks:
        print("[Indexer] No chunks found.")
        return 0

    print(f"[Indexer] Embedding {len(all_chunks)} chunks...")
    all_embeddings = model.encode(all_chunks).tolist()

    # Store in ChromaDB in batches
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            ids=all_ids[i:i + batch_size],
            documents=all_chunks[i:i + batch_size],
            embeddings=all_embeddings[i:i + batch_size],
            metadatas=all_metadata[i:i + batch_size]
        )

    print(f"[Indexer] Done. Indexed {chunk_id} chunks from {codebase_path}")
    return chunk_id