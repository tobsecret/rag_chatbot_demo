import os
import tempfile
import shutil
from unittest.mock import patch
import chromadb
from backend.parser import parse_document, extract_chunks
from backend import db


def test_versioning_flow():
    # 1. Setup - Create a temporary directory for ChromaDB isolation
    temp_dir = tempfile.mkdtemp()
    print(f"\n--- Setting up temporary ChromaDB in {temp_dir} ---")

    test_client = chromadb.PersistentClient(path=temp_dir)
    test_collection = test_client.get_or_create_collection(name="test_chunks")

    # Paths to real test files
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    path_v1 = os.path.join(data_dir, "v1_pages_2to4", "version_test.pdf")
    path_v2 = os.path.join(data_dir, "v2_pages_2to5", "version_test.pdf")
    test_filename = "multi_page_doc.pdf"

    # We patch the global CHROMA_COLLECTION in the backend.db module
    # so that save_to_db uses our temporary test database instead of the real one.
    with patch("backend.db.CHROMA_COLLECTION", test_collection):
        # 2. Upload Version 1 (Pages 2-4)
        print(f"--- Ingesting Version 1: {path_v1} ---")
        with open(path_v1, "rb") as f:
            content_v1 = f.read()

        parsed_v1 = parse_document(test_filename, content_v1)
        chunks_v1 = extract_chunks(parsed_v1)
        db.save_to_db(parsed_v1.metadata, chunks_v1)

        # Verify v1 exists
        res_v1 = test_collection.get(
            where={"filename": test_filename}, include=["metadatas"]
        )
        assert res_v1.get("ids") and len(res_v1["ids"]) > 0
        metadatas_v1 = res_v1.get("metadatas") or [{}]
        assert all(m.get("version") == 1 for m in metadatas_v1 if m)

        # 3. Upload same content again (Deduplication)
        print("\n--- Testing Deduplication (Re-uploading v1) ---")
        db.save_to_db(parsed_v1.metadata, chunks_v1)
        res_dedup = test_collection.get(where={"filename": test_filename})
        # Should not have added more chunks
        assert len(res_dedup["ids"]) == len(res_v1["ids"])

        # 4. Upload Version 2 (Modified content: Pages 2-5)
        print(f"\n--- Ingesting Version 2: {path_v2} ---")
        with open(path_v2, "rb") as f:
            content_v2 = f.read()

        parsed_v2 = parse_document(test_filename, content_v2)
        chunks_v2 = extract_chunks(parsed_v2)
        db.save_to_db(parsed_v2.metadata, chunks_v2)

        # Verify v2 exists separately
        v2_hash = parsed_v2.metadata["artifact"]["file_hash"]
        res_v2 = test_collection.get(
            where={"file_hash": v2_hash}, include=["metadatas"]
        )
        assert res_v2.get("ids") and len(res_v2["ids"]) > 0
        metadatas_v2 = res_v2.get("metadatas") or [{}]
        assert all(m.get("version") == 2 for m in metadatas_v2 if m)

        # Verify both versions exist in the DB for that filename
        all_chunks = test_collection.get(
            where={"filename": test_filename}, include=["metadatas"]
        )
        metadatas_all = all_chunks.get("metadatas") or []
        versions = set(m["version"] for m in metadatas_all if m and "version" in m)
        assert 1 in versions
        assert 2 in versions

    # 5. Teardown - Clean up the temporary directory
    print(f"\n--- Cleaning up {temp_dir} ---")
    shutil.rmtree(temp_dir)

    print(
        "\n✅ Versioning and Deduplication integration test PASSED in isolated environment!"
    )


if __name__ == "__main__":
    test_versioning_flow()
