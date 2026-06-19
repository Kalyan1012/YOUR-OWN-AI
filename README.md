# VectorDB — Build a Vector Database from Scratch

A fully working Vector Database built from scratch with a web UI. Implements **HNSW**, **KD-Tree**, and **Brute Force** search algorithms side-by-side, plus a RAG pipeline powered by a local LLM via Ollama.

> **Note:** This is an educational project designed to demystify how production vector databases like Pinecone, Weaviate, and Chroma function under the hood.

## 🚀 What This Project Does

| Feature | Description |
| :--- | :--- |
| **3 Search Algorithms** | HNSW (production-grade), KD-Tree, Brute Force — run all three and compare speed |
| **768D Real Embeddings** | Uses `nomic-embed-text` via Ollama for true semantic vectors |
| **2D Vector Visualization** | Live HTML5 Canvas scatter plot — watch clusters form in semantic space |
| **Smart RAG Pipeline** | Ask questions about your documents → FAISS retrieves context → local LLM answers |
| **Document Chunking** | Long documents auto-split into overlapping chunks with context preserved |
| **Full REST API** | FastAPI endpoints: embed, query, search, benchmark, health checks |


Your Text 
    │    ▼ 
Ollama (nomic-embed-text)  ← converts text to a 768-dimensional vector
    │    ▼
FAISS + KD-Tree Indexes    ← indexes the vector in multilayer structures
    │    ▼
Semantic Search            ← finds nearest neighbors in vector space
    │    ▼
Ollama (llama3.2)          ← reads retrieved chunks, generates an answer
    │    ▼
Answer


HNSW (Hierarchical Navigable Small World) is the same algorithm used by major vector databases. It builds a multilayer graph where each layer is progressively sparser—searches start at the top layer and zoom in, achieving $O(\log N)$ complexity instead of $O(N)$ for brute force

🛠️ Prerequisites
Python 3.10+

Ollama (runs the local AI models)

Git

🚀 Step-by-Step Setup
Step 1 — Install Dependencies

# Clone the repository
git clone https://github.com/YOUR_USERNAME/VectorDB.git
cd VectorDB

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

Step 2 — Install Ollama & Pull Models
Minimum specs: 8GB RAM recommended.

# Pull the embedding model (~274 MB)
ollama pull nomic-embed-text

# Pull the language model (~2 GB)
ollama pull llama3.2

# Verify Ollama is running:
ollama list

Step 3 — Start the Server
Bash
# Make sure Ollama is running
ollama serve

# In a new terminal, start the FastAPI server
python run.py
Open your browser to: http://localhost:8000

## 🔌 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/embed` | Chunk, embed, and store document |
| **GET** | `/documents` | List all indexed chunks |
| **DELETE** | `/documents` | Clear all data |
| **POST** | `/query` | Search + generate answer |
| **GET** | `/health` | System status and model info |


## 🔍 Algorithm Deep Dive

| Algorithm | Complexity | Accuracy | Best For |
| :--- | :--- | :--- | :--- |
| **Brute Force** | $O(N)$ | 100% | Small datasets, benchmarking |
| **KD-Tree** | $O(\log N)$ | 100% | Low-medium dimensions (≤50D) |
| **HNSW** | $O(\log N)$ | ~99%+ | High dimensions (768D), production |


📁 Project Structure

VectorDB/
├── app/
│   ├── main.py              # FastAPI backend
│   └── static/              # Frontend UI
├── requirements.txt         # Dependencies
├── run.py                   # Server startup
└── README.md

💡 Troubleshooting
Error loading ASGI app: Ensure app/__init__.py exists.

Embedding takes forever: First run downloads models (wait 2–5 minutes).

LLM says "I couldn't find...": Use a larger model or ensure the Relevance Threshold (Distance < 400) is met.