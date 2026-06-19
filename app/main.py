from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
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

# FAISS indexes
brute_force_index = faiss.IndexFlatL2(DIMENSION)
hnsw_index = faiss.IndexHNSWFlat(DIMENSION, 32)

# Relevance threshold
RELEVANCE_THRESHOLD = 400


# ─── KD-Tree Implementation ──────────────────────────────────
class KDNode:
    def __init__(self, point: np.ndarray, index: int, axis: int,
                 left: Optional['KDNode'] = None,
                 right: Optional['KDNode'] = None):
        self.point = point
        self.index = index
        self.axis = axis
        self.left = left
        self.right = right


class KDTreeIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.points: List[np.ndarray] = []
        self.indices: List[int] = []
        self.root: Optional[KDNode] = None
        self.built = False

    def add(self, point: np.ndarray, index: int):
        self.points.append(point.flatten())
        self.indices.append(index)
        self.built = False

    def _build(self, idxs: List[int], depth: int) -> Optional[KDNode]:
        if not idxs:
            return None
        axis = depth % self.dim
        idxs.sort(key=lambda i: self.points[i][axis])
        mid = len(idxs) // 2
        return KDNode(
            point=self.points[idxs[mid]],
            index=self.indices[idxs[mid]],
            axis=axis,
            left=self._build(idxs[:mid], depth + 1),
            right=self._build(idxs[mid + 1:], depth + 1)
        )

    def _ensure_built(self):
        if not self.built and self.points:
            self.root = self._build(list(range(len(self.points))), 0)
            self.built = True

    def _search_node(self, node: KDNode, query: np.ndarray,
                     depth: int, best: List[tuple], k: int):
        if node is None:
            return

        dist = float(np.sum((node.point - query) ** 2))

        if len(best) < k:
            best.append((dist, node.index))
            best.sort(key=lambda x: x[0])
        elif dist < best[-1][0]:
            best[-1] = (dist, node.index)
            best.sort(key=lambda x: x[0])

        axis = depth % self.dim
        diff = query[axis] - node.point[axis]

        near, far = (node.left, node.right) if diff <= 0 else (node.right, node.left)

        self._search_node(near, query, depth + 1, best, k)

        if len(best) < k or (diff ** 2) < best[-1][0]:
            self._search_node(far, query, depth + 1, best, k)

    def search(self, query: np.ndarray, k: int = 1):
        self._ensure_built()
        if not self.root:
            return np.array([[float('inf')]]), np.array([[-1]])

        best = []
        self._search_node(self.root, query.flatten(), 0, best, k)

        best.sort(key=lambda x: x[0])
        distances = [[x[0] for x in best[:k]]]
        indices = [[x[1] for x in best[:k]]]

        return np.array(distances), np.array(indices)


# Initialize KD-Tree
kd_tree_index = KDTreeIndex(DIMENSION)


# ─── Models ─────────────────────────────────────────
class DocumentPayload(BaseModel):
    name: str
    content: str


class QueryPayload(BaseModel):
    text: str
    algorithm: str


# ─── Helper Functions ─────────────────────────────────
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
    v = np.array(vector)
    x = float(v[10])
    y = float(v[100])
    x = np.tanh(x) * 0.4 + 0.5
    y = np.tanh(y) * 0.4 + 0.5
    x += float(np.std(v[0:50])) * 0.3
    y += float(np.std(v[50:150])) * 0.3
    jitter_x = (float(np.sum(v[200:250])) % 10) / 50
    jitter_y = (float(np.sum(v[300:350])) % 10) / 50
    x += jitter_x
    y += jitter_y
    x = max(0.05, min(0.95, x))
    y = max(0.05, min(0.95, y))
    return [x, y]


def ask_llm_general(question: str) -> str:
    try:
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[{'role': 'user', 'content': question}]
        )
        return response['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"


# ─── API Endpoints ──────────────────────────────────
@app.post("/embed")
async def embed_document(payload: DocumentPayload):
    global document_chunks, brute_force_index, hnsw_index, kd_tree_index

    chunks = chunk_text(payload.content)
    inserted_chunks = []

    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        vector_np = np.array([vector], dtype='float32')

        chunk_id = len(document_chunks)
        vector_2d = reduce_to_2d(vector)

        chunk_data = {
            "id": chunk_id,
            "name": f"{payload.name}_chunk_{i}",
            "content": chunk,
            "vector_2d": vector_2d
        }

        document_chunks.append(chunk_data)
        inserted_chunks.append(chunk_data)

        # Add to all indexes
        brute_force_index.add(vector_np)
        hnsw_index.add(vector_np)
        kd_tree_index.add(vector_np, chunk_id)

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

    # Route to correct algorithm
    algo = payload.algorithm.lower()
    k = 1
    steps.append(f"Running {algo.upper()} search across {len(document_chunks)} vectors...")

    if algo == "hnsw":
        distances, indices = hnsw_index.search(q_vec_np, k)
    elif algo == "kdtree":  # ✅ Fixed: kdtree instead of kd_tree
        distances, indices = kd_tree_index.search(q_vec_np, k)
    else:  # brute_force
        distances, indices = brute_force_index.search(q_vec_np, k)

    search_time = (time.time() - start_time) * 1000
    closest_idx = int(indices[0][0])
    raw_distance = float(distances[0][0])

    steps.append(f"Closest match found at distance {raw_distance:.2f}")

    # RAG mode if relevant
    if closest_idx != -1 and raw_distance < RELEVANCE_THRESHOLD:
        matched_chunk = document_chunks[closest_idx]
        node_name = matched_chunk["name"]
        content = matched_chunk["content"]

        steps.append(f"✅ Relevant document: {node_name}")
        steps.append("Returning document content...")

        doc_name = node_name.split('_chunk_')[0] if '_chunk_' in node_name else node_name

        return {
            "query_vector": q_vec_2d,
            "closest_node": node_name,
            "closest_node_vector": matched_chunk["vector_2d"],
            "distance": raw_distance,
            "response": f"<strong>📄 From your document '{doc_name}':</strong><br><br>{content}",
            "algorithm_used": algo.upper(),
            "search_time": round(search_time, 2),
            "context": content,
            "mode": "rag",
            "steps": steps
        }

    # General mode
    else:
        if closest_idx != -1:
            doc_name = document_chunks[closest_idx]["name"].split('_chunk_')[0]
            steps.append(f"❌ '{doc_name}' not relevant (distance {raw_distance:.2f})")

        steps.append("🧠 Using General AI...")
        response = ask_llm_general(payload.text)
        steps.append("General answer generated")

        return {
            "query_vector": q_vec_2d,
            "closest_node": "🧠 General AI",
            "distance": raw_distance,
            "response": f"<strong>🧠 General AI Answer:</strong><br><br>{response}",
            "algorithm_used": algo.upper(),
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
    global document_chunks, brute_force_index, hnsw_index, kd_tree_index
    document_chunks = []
    brute_force_index = faiss.IndexFlatL2(DIMENSION)
    hnsw_index = faiss.IndexHNSWFlat(DIMENSION, 32)
    kd_tree_index = KDTreeIndex(DIMENSION)
    return {"status": "cleared"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "documents": len(document_chunks),
        "algorithms": ["HNSW", "KD-Tree", "Brute Force"],
        "models": ["nomic-embed-text", "llama3.2:1b"]
    }


@app.get("/")
async def read_root():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)