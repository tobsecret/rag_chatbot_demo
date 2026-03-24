from typing import List, Dict, Any
from backend.retriever import get_retriever

def search_documents(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the internal document knowledge base for relevant information.
    
    This tool should be used by the agent whenever the user asks a question 
    about uploaded documents, concepts, or specific data points that might 
    be stored in the system.
    
    Args:
        query (str): The natural language search query or question.
        max_results (int): The maximum number of relevant chunks to return (default: 5).
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the relevant text chunks 
        and their associated metadata (like filename and original headings).
    """
    print(f"Agent Tool Invoked: search_documents(query='{query}', max_results={max_results})")
    
    # Instantiate the decoupled retrieval layer
    retriever = get_retriever()
    
    # Execute the semantic search
    results = retriever.search_chunks(query_text=query, top_k=max_results)
    
    return results
