# VectorDB Python Engine 🚀

A high-performance **Vector Database** built from scratch in Python. It implements a production-grade **RAG (Retrieval-Augmented Generation)** pipeline, leveraging **FAISS** for high-dimensional indexing and **Ollama** for local LLM inference.

This project demonstrates the fundamental mechanics of how industry-standard vector databases (like Pinecone, Weaviate, or Chroma) operate under the hood.

---

## 🛠️ Key Features
| Feature | Description |
| :--- | :--- |
| **Search Engine** | Uses **FAISS** (Meta AI) for high-performance HNSW graph indexing. |
| **Embedding Logic** | Converts text to 768D vectors using `nomic-embed-text`. |
| **RAG Pipeline** | Context-aware Q&A powered by local `llama3.2:1b`. |
| **2D Visualization** | Live projection of high-dimensional space on a web canvas. |
| **Context Handling** | Sliding-window overlapping chunker to maintain semantic boundaries. |
| **API Driven** | Full REST interface via **FastAPI** for CRUD operations. |

---

## 🏗️ Architecture Flow



1. **Embedding:** User text is converted to a 768D semantic vector.
2. **Indexing:** Vectors are stored in a **FAISS HNSW** graph for sub-millisecond retrieval.
3. **Retrieval:** The system performs similarity search to find relevant context.
4. **Inference:** Relevant chunks are passed to the **LLM (Llama 3.2)** to generate a grounded, hallucination-free answer.

---

## 🚀 Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- [Ollama](https://ollama.com) installed and running in the background.

### 2. Install Dependencies
```bash
pip install fastapi uvicorn pydantic numpy faiss-cpu ollama


3. Pull AI Models
Bash
ollama pull nomic-embed-text
ollama pull llama3.2:1b
4. Launch the Server
Bash
python main.py
Open http://127.0.0.1:8000 in your browser.


🧠 Why this Architecture?Why FAISS? Unlike basic Python lists, FAISS is built in C++ and uses SIMD instructions to perform high-dimensional math in microseconds.Why HNSW? In high dimensions (768D), traditional tree-based partitioning (like KD-Trees) suffers from the Curse of Dimensionality. HNSW overcomes this by building a graph of small-world connections, ensuring $O(\log N)$ search speeds even at scale.Safety Gate: The engine includes a relevance threshold. If the vector distance is too high, the system automatically defaults to general AI mode, preventing the model from hallucinating based on unrelated data.🌐 REST API Reference