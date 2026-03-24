import chromadb

CHROMA_CLIENT = chromadb.PersistentClient(path="./chroma_data")
CHROMA_COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="beakr_chunks")


def save_to_chromadb(meta_data: dict, chunks: list[dict]) -> None:
    """
    Saves the chunk texts and their semantic vector embeddings to ChromaDB.
    """
    file_hash = meta_data["artifact"]["file_hash"]

    # Prevent duplicate ingestion by checking if any chunks with this hash exist
    existing = CHROMA_COLLECTION.get(where={"file_hash": file_hash}, limit=1)
    if existing and existing["ids"] and len(existing["ids"]) > 0:
        print(f"Skipping Chroma insertion: File with hash {file_hash} already exists.")
        return

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        # We need a unique ID for every chunk
        chunk_id = f"{file_hash}_chunk_{i}"

        ids.append(chunk_id)
        if "vector" in chunk:
            embeddings.append(chunk["vector"])

        documents.append(chunk.get("text", ""))

        # Flatten the metadata to store in Chroma (it doesn't support nested dicts)
        safe_meta = {
            "file_hash": file_hash,
            "filename": str(meta_data["artifact"].get("filename", "")),
            "file_type": str(meta_data["artifact"].get("file_type", "")),
            "chunk_type": str(chunk.get("chunk_type", "text")),
        }

        headings = chunk.get("headings", [])
        if headings and isinstance(headings, list):
            safe_meta["headings"] = " > ".join(headings)

        metadatas.append(safe_meta)

    if ids:
        try:
            CHROMA_COLLECTION.add(
                ids=ids,
                embeddings=embeddings if embeddings else None,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as e:
            print(f"Error saving to ChromaDB: {e}")


def save_to_db(meta_data: dict, chunks: list[dict]) -> None:
    """
    Saves the extracted document to all configured databases.
    Currently routing entirely to ChromaDB for Semantic Search.
    """
    print("Saving document chunks to storage layer...")
    save_to_chromadb(meta_data, chunks)
    print("Document chunks successfully saved to ChromaDB.")
