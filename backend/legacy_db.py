from elasticsearch import Elasticsearch
import duckdb
import json
from typing import Any

DB_FILE = "beakr.duckdb"
ES_CLIENT = Elasticsearch("http://localhost:9200")
ES_INDEX = "beakr_documents"


def init_db():
    """Builds the database tables if they do not exist."""
    with duckdb.connect(DB_FILE) as con:
        con.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_doc_id;
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER DEFAULT nextval('seq_doc_id'),
                filename VARCHAR,
                file_hash VARCHAR UNIQUE,
                artifact_metadata JSON,
                extracted_metadata JSON,
                system_metadata JSON,
                full_text TEXT,
                upload_timestamp TIMESTAMP
            );
        """)


def save_to_duckdb(meta_data: dict, document_obj: Any) -> None:
    """
    Saves the extracted document metadata and full text to DuckDB.
    Uses file_hash to deduplicate uploads.
    """
    init_db()

    # Extract the full text using Docling's built-in export method
    full_text = document_obj.export_to_text()

    file_hash = meta_data["artifact"]["file_hash"]

    with duckdb.connect(DB_FILE) as con:
        # Simple deduplication check
        exists = con.execute(
            "SELECT id FROM documents WHERE file_hash = ?", [file_hash]
        ).fetchone()

        if exists:
            print(
                f"Skipping insertion: File with hash {file_hash} already exists in database."
            )
            # For a "true" versioning system, you would increment version numbers here
            # instead of skipping completely.
            return

        # Serialize metadata to JSON strings to easily store them in DuckDB's JSON columns
        artifact_json = json.dumps(meta_data.get("artifact", {}))
        extracted_json = json.dumps(meta_data.get("extracted", {}))
        system_json = json.dumps(meta_data.get("system", {}))

        # Insert the record
        con.execute(
            """
            INSERT INTO documents (
                filename, 
                file_hash, 
                artifact_metadata, 
                extracted_metadata, 
                system_metadata, 
                full_text, 
                upload_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                meta_data["artifact"]["filename"],
                file_hash,
                artifact_json,
                extracted_json,
                system_json,
                full_text,
                meta_data["artifact"]["upload_timestamp"],
            ],
        )


def init_es():
    """Builds the Elasticsearch index mapping if it does not exist."""
    try:
        if not ES_CLIENT.indices.exists(index=ES_INDEX):
            ES_CLIENT.indices.create(
                index=ES_INDEX,
                mappings={
                    "properties": {
                        "filename": {"type": "keyword"},
                        "file_hash": {"type": "keyword"},
                        "artifact_metadata": {"type": "object"},
                        "extracted_metadata": {"type": "object"},
                        "system_metadata": {"type": "object"},
                        "full_text": {"type": "text"},
                        "upload_timestamp": {"type": "date"},
                    }
                },
            )
    except Exception as e:
        print(f"Warning: Could not initialize Elasticsearch index: {e}")


def save_to_elasticsearch(meta_data: dict, document_obj: Any) -> None:
    """
    Saves the extracted document metadata and full text to Elasticsearch for text search.
    """
    init_es()

    full_text = document_obj.export_to_text()
    file_hash = meta_data["artifact"]["file_hash"]

    try:
        # Check if hash already exists in ES
        response = ES_CLIENT.search(
            index=ES_INDEX, query={"term": {"file_hash": file_hash}}, size=1
        )

        # In newer elasticsearch client, response format has changed but value is checked roughly the same
        # Let's cleanly handle both cases (object or dict mapping)
        total_hits = (
            response.get("hits", {}).get("total", {}).get("value", 0)
            if isinstance(response, dict)
            else response.hits.total.value
        )
        if total_hits > 0:
            print(
                f"Skipping ES insertion: File with hash {file_hash} already exists in Elasticsearch."
            )
            return

        doc = {
            "filename": meta_data["artifact"]["filename"],
            "file_hash": file_hash,
            "artifact_metadata": meta_data.get("artifact", {}),
            "extracted_metadata": meta_data.get("extracted", {}),
            "system_metadata": meta_data.get("system", {}),
            "full_text": full_text,
            "upload_timestamp": meta_data["artifact"]["upload_timestamp"],
        }

        ES_CLIENT.index(index=ES_INDEX, document=doc)
    except Exception as e:
        print(f"Error saving to Elasticsearch: {e}")
