from backend.embedder import get_model
from backend.generator import get_generator
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker

print("--- Pre-loading Embedding model ---")

get_model()

print("\n--- Pre-loading Text Generation model ---")

get_generator()

print("\n--- Pre-loading Docling Layout & OCR models ---")

# Instantiating the converter triggers the download of the docling models
DocumentConverter()

print("\n--- Pre-loading Docling Chunking models ---")
HierarchicalChunker()

print("\nAll heavy AI models successfully pre-loaded and cached into the image!")
