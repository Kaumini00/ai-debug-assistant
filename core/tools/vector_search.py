import chromadb
from sentence_transformers import SentenceTransformer
from core.tools.indexer import get_collection

model = SentenceTransformer("all-MiniLM-L6-v2")

def vector_search(codebase_path: str, query: str, top_k: int = 5) -> list:
    """
    Search the ChromaDB collection for code chunks
    semantically similar to the query (error message).
    Returns top_k most relevant chunks.
    """
    try:
        collection = get_collection(codebase_path)

        # Check if collection has data
        existing = collection.get()
        if not existing["ids"]:
            return [{"error": "Codebase not indexed yet. Call /agent/index first."}]

        # Convert query to vector
        query_embedding = model.encode([query]).tolist()

        # Search ChromaDB for closest vectors
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, len(existing["ids"]))
        )

        # Format results
        matches = []
        for i, doc in enumerate(results["documents"][0]):
            matches.append({
                "chunk": doc,
                "file": results["metadatas"][0][i]["file"],
                "start_line": results["metadatas"][0][i]["start_line"],
                "end_line": results["metadatas"][0][i]["end_line"],
                "similarity_score": round(1 - results["distances"][0][i], 3)
            })

        return matches

    except Exception as e:
        return [{"error": f"Vector search failed: {str(e)}"}]