from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import numpy as np
from app.search import BruteForceEngine, KDTreeEngine

app = FastAPI()

# Core Data Stores and Search Engines
raw_database = []
brute_engine = BruteForceEngine()
kd_engine = KDTreeEngine()

# --- Request Data Structures ---
class DocumentPayload(BaseModel):
    name: str
    content: str

class QueryPayload(BaseModel):
    text: str
    algorithm: str


# --- Helper Embedding Function ---
def generate_pseudo_embedding(text: str):
    """
    Simulates a text embedding model by reducing any string down to 
    a deterministic 2D coordinate [X, Y] between 0.0 and 1.0.
    """
    hash_val = sum(ord(char) for char in text)
    np.random.seed(hash_val)
    return np.random.rand(2).tolist()


# --- API Routes ---

@app.post("/embed")
def embed_document(payload: DocumentPayload):
    # 1. Turn document text into an [X, Y] coordinate
    vector = generate_pseudo_embedding(payload.content)
    item = {"name": payload.name, "vector": vector, "content": payload.content}
    
    # 2. Feed the vector data into both search engines
    raw_database.append(item)
    brute_engine.add(payload.name, vector, payload.content)
    
    # Rebuild the KD-Tree structure since a new node was introduced
    kd_engine.root = kd_engine.build(list(raw_database))
    
    return {"status": "success", "vector": vector}

@app.post("/query")
def process_query(payload: QueryPayload):
    # 1. Turn query text into an [X, Y] coordinate
    q_vec = generate_pseudo_embedding(payload.text)
    
    # 2. Pick the engine based on user preference
    algo = payload.algorithm.lower()
    if algo == "kd_tree" and kd_engine.root is not None:
        name, dist, content = kd_engine.search(q_vec)
    else:
        name, dist, content = brute_engine.search(q_vec)
        
    # 3. Handle threshold context gating to block AI hallucinations
    if dist < 0.6:
        response = f"Context matched inside {name}! Fact confirmation: '{content}'."
    else:
        response = "Context mismatch! The data point is too far away. Rejecting to prevent hallucination."

    return {
        "query_vector": q_vec,
        "closest_node": name,
        "distance": dist,
        "response": response
    }