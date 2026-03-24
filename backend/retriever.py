from typing import Protocol, List, Dict, Any
from backend.embedder import generate_embedding

# --- PORT (Hexagonal Architecture Interface) ---


class DocumentRetriever(Protocol):
    def search_chunks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches for the most relevant document chunks based on semantic similarity."""
        ...


# --- ADAPTER (ChromaDB Implementation) ---


class ChromaRetriever:
    def __init__(self):
        # Import at runtime to ensure db has initialized and collection is available
        from backend.db import CHROMA_COLLECTION

        self.collection = CHROMA_COLLECTION

    def search_chunks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Implements the retrieval logic using ChromaDB.
        Embeds the query text and performs a vector search against the chunks.
        """
        # 1. Embed the user's query into a vector representation
        query_vector = generate_embedding(query_text)
        if not query_vector:
            return []

        # 2. Search ChromaDB using the vector
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # 3. Format the raw Chroma results into a clean list of dictionaries
        retrieved_chunks = []

        # Chroma returns lists of lists since it supports batch queries
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = (
                results["metadatas"][0]  # type: ignore
                if results.get("metadatas")
                else [{}] * len(docs)
            )
            distances = (
                results["distances"][0]  # type: ignore
                if results.get("distances")
                else [0.0] * len(docs)
            )

            for doc, meta, dist in zip(docs, metas, distances):
                retrieved_chunks.append(
                    {"text": doc, "metadata": meta, "similarity_distance": dist}
                )

        return retrieved_chunks


# --- DEPENDENCY INJECTION ---


def get_retriever() -> DocumentRetriever:
    """Factory method representing the DI layer for the application."""
    return ChromaRetriever()
