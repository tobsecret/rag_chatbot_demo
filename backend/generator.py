from transformers import pipeline
import torch

# We use an incredibly small instruction-tuned model explicitly designed to run on CPUs
# for local non-GPU showcases.
MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        print(f"\n🤖 Loading tiny showcase LLM {MODEL_ID}... (This may take a moment to download initially)\n")
        
        try:
            _generator = pipeline(
                "text-generation", 
                model=MODEL_ID, 
                device_map="cpu",
                torch_dtype=torch.float32
            )
        except Exception as e:
            print(f"Error initializing model: {e}")
            raise e
            
    return _generator

def answer_question(query: str, context_chunks: list[dict]) -> str:
    """
    Constructs a RAG prompt and asks the tiny LLM to synthesize an 
    answer based solely on the retrieved internal document contexts.
    """
    if not context_chunks:
        return "I couldn't find any relevant information in your uploaded documents to answer that."
        
    # Build the context string from our structured ChromaDB dictionary
    context_text = ""
    for chunk in context_chunks:
        text = chunk.get("text", "")
        meta = chunk.get("metadata", {})
        source = meta.get("filename", "Unknown File")
        
        context_text += f"--- Excerpt from {source} ---\n"
        context_text += f"{text}\n\n"
        
    # Using standard ChatML template formatting for the model
    prompt = f"""<|im_start|>system
You are a helpful AI assistant analyzing user documents. 
Using only the Context provided below, concisely answer the user's Question. If the answer cannot be deduced from the Context, say "I do not know based on the provided documents."<|im_end|>
<|im_start|>user
Context:
{context_text}

Question: {query}<|im_end|>
<|im_start|>assistant
"""
    
    print("\n🧠 Synthesizing answer based on context...")
    gen = get_generator()
    
    # Run the generation. Keep it relatively short for the tiny CPU model.
    result = gen(prompt, max_new_tokens=150, return_full_text=False)
    
    answer = result[0]["generated_text"].strip()
    return answer
