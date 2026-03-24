from sentence_transformers import SentenceTransformer

# Using a small, fast HuggingFace model optimized for semantic retrieval
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model():
    print(f"Loading embedding model {MODEL_NAME}...")
    _model = SentenceTransformer(MODEL_NAME)
    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Generates a dense vector embedding for a single string of text.
    """
    if not text or not text.strip():
        return []

    m = get_model()
    # encode() returns a numpy array, we convert to standard python list
    return m.encode(text).tolist()


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Takes a list of chunk dictionaries, encodes their text in batch,
    and appends a 'vector' field to each dictionary.
    """
    if not chunks:
        return []

    m = get_model()

    # Batch extraction is much faster than encoding one by one
    texts = [c.get("text", "") for c in chunks]
    embeddings = m.encode(texts)

    for i, chunk in enumerate(chunks):
        chunk["vector"] = embeddings[i].tolist()

    return chunks
