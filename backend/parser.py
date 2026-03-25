import os
import tempfile
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.chunking import HierarchicalChunker

@dataclass
class ParsedDocument:
    metadata: dict
    document_obj: Any

def extract_metadata(filename: str, file_content: bytes, doc_obj: Any) -> dict:
    """
    Extracts comprehensive metadata from the file and the parsed document object.
    Includes artifact-level, intrinsic (extracted), and system metadata.
    """
    # 1. Artifact-level metadata
    file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
    file_hash = hashlib.sha256(file_content).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    
    artifact_metadata = {
        "filename": filename,
        "file_type": file_type,
        "size_bytes": len(file_content),
        "upload_timestamp": now,
        "file_hash": file_hash,
    }
    
    # 2. Extracted (intrinsic) metadata
    # We attempt to extract safe defaults or structural indicators based on the 
    # structure of a docling document_obj if available.
    extracted_metadata = {
        # Docling defaults the name to the temporary file we created, so we use the real filename instead.
        "title": filename,
        "author": "unknown",  # Could be refined depending on doc_obj structure
        "page_count": 0,      # Could be updated if doc_obj exposes pages
        "structural_signals": "sections, headings, tables"  # General summary
    }
    
    # 3. System metadata
    system_metadata = {
        "uploaded_by": "mock_user_1",
        "version_number": 1,
        "first_seen": now,
        "last_seen": now
    }
    
    return {
        "artifact": artifact_metadata,
        "extracted": extracted_metadata,
        "system": system_metadata
    }

def parse_document(filename: str, file_content: bytes) -> ParsedDocument:
    """
    Parses a document (PDF, DOCX, etc.) using IBM Docling.
    """
    # 1. Create leaner pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False
    
    # 2. Tell the converter to use these options for PDFs
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    # Docling often requires a file path to know the format, so we write to a temporary file
    # We maintain the original file extension
    ext = ""
    if "." in filename:
        ext = f".{filename.split('.')[-1]}"
        
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
        
    try:
        # Convert the document
        result = converter.convert(temp_file_path)
        
        # Return structured metadata and the parsed Docling document object
        metadata = extract_metadata(filename, file_content, result.document)
        
        return ParsedDocument(
            metadata=metadata,
            document_obj=result.document,
        )
        
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def extract_chunks(parsed_doc: ParsedDocument) -> list[dict]:
    """
    Uses Docling's HierarchicalChunker to break the document down into functional chunks 
    (paragraphs, tables, lists) and preserves necessary context like headings for RAG.
    """
    chunker = HierarchicalChunker()
    
    # Generate chunk iterables from the docling object
    docling_chunks = chunker.chunk(parsed_doc.document_obj)
    
    structured_chunks = []
    for i, c in enumerate(docling_chunks):
        chunk_type = "text"
        chunk_text = c.text
        
        # Identify if chunk is a table or picture to explicitly format it
        doc_items = getattr(c.meta, "doc_items", [])
        if isinstance(doc_items, list):
            for item in doc_items:
                # In Docling, label specifies the element type
                item_label = getattr(item, "label", "")
                if str(item_label).lower() == "table":
                    chunk_type = "table"
                    # Guaranteed markdown export for LLMs to retain structure
                    if hasattr(item, "export_to_markdown"):
                        chunk_text = item.export_to_markdown()
                    break
                    
        # Generate a unique hash for the chunk text for granular deduplication
        chunk_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
                    
        # Extract meaningful RAG details to store in our database/vector store.
        structured_chunks.append({
            "chunk_id": i,
            "chunk_type": chunk_type,
            "text": chunk_text,
            "chunk_hash": chunk_hash,
            "headings": getattr(c.meta, "headings", []),
            "source_filename": parsed_doc.metadata["artifact"]["filename"],
            "file_hash": parsed_doc.metadata["artifact"]["file_hash"]
        })
        
    return structured_chunks
