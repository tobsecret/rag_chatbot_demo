import chromadb

CHROMA_CLIENT = chromadb.PersistentClient(path="./chroma_data")
CHROMA_COLLECTION = CHROMA_CLIENT.get_or_create_collection(name="beakr_chunks")


def save_to_chromadb(meta_data: dict, chunks: list[dict]) -> None:
    """
    Saves the chunk texts and their semantic vector embeddings to ChromaDB.
    Handles deduplication and versioning.
    """
    file_hash = meta_data["artifact"]["file_hash"]
    filename = meta_data["artifact"]["filename"]

    # 1. Strict Deduplication: Check if this exact content already exists
    existing_content = CHROMA_COLLECTION.get(where={"file_hash": file_hash}, limit=1)
    if existing_content and existing_content["ids"] and len(existing_content["ids"]) > 0:
        print(f"Skipping Chroma insertion: File with hash {file_hash} already exists.")
        return

    # 2. Versioning: Check if this is a new version of an existing file (by name)
    # Note: A more advanced version would also check for chunk-level similarity/overlap.
    existing_versions = CHROMA_COLLECTION.get(
        where={"filename": filename},
        include=["metadatas"]
    )
    
    max_version = 0
    first_seen = meta_data["artifact"]["upload_timestamp"]
    
    if existing_versions and existing_versions["metadatas"]:
        for m in existing_versions["metadatas"]:
            if not m:
                continue
            ver = m.get("version", 1)
            if isinstance(ver, int) and ver > max_version:
                max_version = ver
            
            # Carry over the first_seen timestamp from the original version
            f_seen = m.get("first_seen")
            if f_seen:
                first_seen = f_seen
                
    new_version = max_version + 1
    if new_version > 1:
        print(f"Detected new version (v{new_version}) for file: {filename}")

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

        # Flatten the metadata to store in Chroma
        safe_meta = {
            "file_hash": file_hash,
            "filename": str(filename),
            "file_type": str(meta_data["artifact"].get("file_type", "")),
            "chunk_type": str(chunk.get("chunk_type", "text")),
            "chunk_hash": str(chunk.get("chunk_hash", "")),
            "version": new_version,
            "first_seen": str(first_seen),
            "last_seen": str(meta_data["artifact"]["upload_timestamp"]),
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
