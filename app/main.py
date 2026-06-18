from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import numpy as np
import faiss
import ollama
import time
from pathlib import Path

app = FastAPI(title="Vector RAG System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

document_chunks: List[Dict] = []
DIMENSION = 768

brute_force_index = faiss.IndexFlatL2(DIMENSION)
hnsw_index = faiss.IndexHNSWFlat(DIMENSION, 32)

RELEVANCE_THRESHOLD = 300

class DocumentPayload(BaseModel):
    name: str
    content: str

class QueryPayload(BaseModel):
    text: str
    algorithm: str

def get_embedding(text: str) -> List[float]:
    try:
        response = ollama.embeddings(model="nomic-embed-text", prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return np.random.rand(DIMENSION).tolist()

def chunk_text(text: str, max_words=100, overlap=20) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words - overlap):
        chunk = " ".join(words[i:i + max_words])
        chunks.append(chunk)
        if i + max_words >= len(words):
            break
    return chunks if chunks else [text]

def reduce_to_2d(vector: List[float]) -> List[float]:
    """Spread vectors evenly across full canvas"""
    v = np.array(vector)
    
    # Use actual dimensions (not averages) so different docs spread out
    x = float(v[10])   # Pick dimension 10
    y = float(v[100])  # Pick dimension 100
    
    # Use tanh to map ANY value to 0-1 range (sigmoid spread)
    x = np.tanh(x) * 0.4 + 0.5  # Now spreads 0.1 to 0.9
    y = np.tanh(y) * 0.4 + 0.5
    
    # Add unique fingerprint from standard deviation so similar docs separate
    x += float(np.std(v[0:50])) * 0.3
    y += float(np.std(v[50:150])) * 0.3
    
    # Random but deterministic jitter based on vector sum (so same doc = same spot)
    jitter_x = (float(np.sum(v[200:250])) % 10) / 50
    jitter_y = (float(np.sum(v[300:350])) % 10) / 50
    
    x += jitter_x
    y += jitter_y
    
    # Clamp to full canvas spread
    x = max(0.05, min(0.95, x))
    y = max(0.05, min(0.95, y))
    
    return [x, y]

def ask_llm_general(question: str) -> str:
    """General knowledge mode - only used when no relevant doc found"""
    try:
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role': 'user', 'content': question}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

@app.post("/embed")
async def embed_document(payload: DocumentPayload):
    global document_chunks, brute_force_index, hnsw_index

    chunks = chunk_text(payload.content)
    inserted_chunks = []

    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        vector_np = np.array([vector], dtype='float32')
        vector_2d = reduce_to_2d(vector)

        chunk_data = {
            "id": len(document_chunks),
            "name": f"{payload.name}_chunk_{i}",
            "content": chunk,
            "vector_2d": vector_2d
        }

        document_chunks.append(chunk_data)
        inserted_chunks.append(chunk_data)

        brute_force_index.add(vector_np)
        hnsw_index.add(vector_np)

    return {
        "status": "success",
        "chunks_inserted": len(chunks),
        "chunks": inserted_chunks,
        "total_chunks": len(document_chunks)
    }

@app.post("/query")
async def process_query(payload: QueryPayload):
    start_time = time.time()
    steps = []
    
    steps.append("Generating query embedding...")
    q_vec = get_embedding(payload.text)
    q_vec_np = np.array([q_vec], dtype='float32')
    q_vec_2d = reduce_to_2d(q_vec)
    
    # No documents - General mode
    if not document_chunks:
        steps.append("No documents - using General AI")
        
        response = ask_llm_general(payload.text)
        search_time = (time.time() - start_time) * 1000
        
        return {
            "query_vector": q_vec_2d,
            "closest_node": "🧠 General AI",
            "distance": 0.0,
            "response": response,
            "algorithm_used": "GENERAL",
            "search_time": round(search_time, 2),
            "mode": "general",
            "steps": steps
        }
    
    # Search documents
    steps.append(f"Searching {len(document_chunks)} documents with {payload.algorithm.upper()}...")
    
    k = 1
    if payload.algorithm.lower() == "hnsw":
        distances, indices = hnsw_index.search(q_vec_np, k)
    else:
        distances, indices = brute_force_index.search(q_vec_np, k)
    
    closest_idx = int(indices[0][0])
    raw_distance = float(distances[0][0])
    search_time = (time.time() - start_time) * 1000
    
    steps.append(f"Closest match found at distance {raw_distance:.2f}")
    
    # RAG mode - document is relevant
    if closest_idx != -1 and raw_distance < RELEVANCE_THRESHOLD:
        matched_chunk = document_chunks[closest_idx]
        node_name = matched_chunk["name"]
        content = matched_chunk["content"]
        
        steps.append(f"✅ Relevant document found: {node_name}")
        steps.append("Returning your document content directly...")
        
        doc_name = node_name.split('_chunk_')[0] if '_chunk_' in node_name else node_name
        
        # ✅ NO LLM! Just return your exact text
        return {
            "query_vector": q_vec_2d,
            "closest_node": node_name,
            "closest_node_vector": matched_chunk["vector_2d"],
            "distance": raw_distance,
            "response": f"<strong>📄 From your document '{doc_name}':</strong><br><br>{content}",
            "algorithm_used": payload.algorithm.upper(),
            "search_time": round(search_time, 2),
            "context": content,
            "mode": "rag",
            "steps": steps
        }
    
    # General mode - document not relevant
    else:
        if closest_idx != -1:
            matched_chunk = document_chunks[closest_idx]
            doc_name = matched_chunk["name"].split('_chunk_')[0] if '_chunk_' in matched_chunk["name"] else matched_chunk["name"]
            steps.append(f"❌ '{doc_name}' not relevant (distance {raw_distance:.2f})")
        
        steps.append("🧠 Using General AI...")
        
        response = ask_llm_general(payload.text)
        steps.append("General answer generated")
        
        return {
            "query_vector": q_vec_2d,
            "closest_node": "🧠 General AI",
            "distance": raw_distance,
            "response": f"<strong>🧠 General AI Answer:</strong><br><br>{response}",
            "algorithm_used": payload.algorithm.upper(),
            "search_time": round(search_time, 2),
            "mode": "general",
            "steps": steps
        }

@app.get("/documents")
async def get_documents():
    return {
        "total": len(document_chunks),
        "chunks": document_chunks
    }

@app.delete("/documents")
async def clear_documents():
    global document_chunks, brute_force_index, hnsw_index
    document_chunks = []
    brute_force_index = faiss.IndexFlatL2(DIMENSION)
    hnsw_index = faiss.IndexHNSWFlat(DIMENSION, 32)
    return {"status": "cleared"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "documents": len(document_chunks),
        "models": ["nomic-embed-text", "llama3.2:1b"]
    }

@app.get("/")
async def read_root():
    return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)