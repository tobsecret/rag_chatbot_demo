from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.parser import parse_document, extract_metadata, extract_chunks
from backend.db import save_to_db, CHROMA_COLLECTION
from backend.embedder import embed_chunks
from backend.agent_tools import search_documents as rag_retriever_tool
from backend.generator import answer_question

app = FastAPI()

# Important: Allow your Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    # 1. Read the file
    file_content = await file.read()

    # 2. Parse the PDF/DOCX (Returns metadata and text/structured data)
    filename = file.filename or "unknown_document"
    parsed_data = parse_document(filename, file_content)
    meta_data = extract_metadata(filename, file_content, parsed_data.document_obj)

    # 3. Extract chunks
    chunks = extract_chunks(parsed_data)
    
    # 4. Generate Semantic Embeddings for the chunks
    embedded_chunks = embed_chunks(chunks)
    
    # 5. Save the chunks and embeddings to the Vector Database
    save_to_db(meta_data, embedded_chunks)

    return {
        "message": "Success",
        "filename": file.filename,
        "metadata": meta_data,
        "chunks_processed": len(embedded_chunks),
        "chunks_preview": embedded_chunks[:1]  # preview just 1 chunk so we don't flood the UI with 384 floats
    }


@app.get("/api/documents")
async def list_documents():
    """Returns a list of unique document filenames currently stored in the DB."""
    try:
        results = CHROMA_COLLECTION.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
        
        unique_docs = {}
        for m in metadatas:
            if not m:
                continue
            f_hash = m.get("file_hash")
            f_name = m.get("filename")
            if f_hash and f_name and f_hash not in unique_docs:
                unique_docs[f_hash] = {
                    "filename": f_name,
                    "file_hash": f_hash,
                    "file_type": m.get("file_type", ""),
                    "version": m.get("version", 1),
                    "first_seen": m.get("first_seen"),
                    "last_seen": m.get("last_seen")
                }
                
        return {"documents": list(unique_docs.values())}
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return {"documents": []}

class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # 1. AI Agent invokes its `search_documents` tool to query the vector database
    retrieved_chunks = rag_retriever_tool(query=request.query, max_results=3)
    
    # 2. The RAG architecture synthesizes the final answer using the retrieved context
    final_answer = answer_question(query=request.query, context_chunks=retrieved_chunks)
    
    # We return both the generated answer and the exact context citations used to form it!
    # Returning the citations allows the frontend UI to display "Proof" to the user!
    return {
        "answer": final_answer,
        "sources": retrieved_chunks
    }
