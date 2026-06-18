# VectorDB Python Engine 🚀

A high-performance **Vector Database** built from scratch in Python. It implements a production-grade **RAG (Retrieval-Augmented Generation)** pipeline, leveraging **FAISS** for high-dimensional indexing and **Ollama** for local LLM inference.

This project demonstrates the fundamental mechanics of how industry-standard vector databases (like Pinecone, Weaviate, or Chroma) operate under the hood.


A production-inspired Vector Database and RAG Engine built entirely in Python.

This project demonstrates how modern AI systems such as ChatGPT with custom knowledge, enterprise search engines, and document assistants retrieve relevant information from large datasets using vector similarity search before generating responses.

Instead of relying on managed services, this implementation builds the core retrieval pipeline from scratch using FAISS, FastAPI, Ollama, and local embedding models.

Overview

Traditional databases search by exact matches.

Vector databases search by meaning.

For example:

Query:

"How does HNSW indexing work?"

The system can retrieve documents containing:

Hierarchical Navigable Small Worlds
Approximate Nearest Neighbor Search
Vector Graph Traversal

even if those exact words do not appear in the query.

This is the foundation of modern Retrieval-Augmented Generation (RAG) systems.

Key Features
Semantic Search

Transforms text into high-dimensional embeddings and retrieves semantically similar content.

High-Speed Vector Indexing

Uses Meta AI's FAISS library with HNSW indexing for efficient nearest-neighbor search.

Local AI Inference

Runs entirely offline using Ollama and Llama 3.2, eliminating dependence on cloud APIs.

Retrieval-Augmented Generation (RAG)

Enhances LLM responses using retrieved context from indexed documents.

Context-Aware Chunking

Implements overlapping chunk windows to preserve semantic continuity across documents.

Interactive Visualization

Projects high-dimensional vector spaces into 2D for exploration and debugging.

REST API

Provides FastAPI endpoints for indexing, searching, and querying documents.

System Architecture
                    ┌─────────────────┐
                    │ User Document   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Text Chunking   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Embedding Model │
                    │ nomic-embed-text│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ FAISS Index     │
                    │ HNSW Graph      │
                    └────────┬────────┘
                             │
                             ▼
                     Similarity Search
                             │
                             ▼
                    ┌─────────────────┐
                    │ Retrieved Docs  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Llama 3.2       │
                    │ Local Inference │
                    └────────┬────────┘
                             │
                             ▼
                       Final Answer
Technology Stack
Component	Technology
Language	Python
API Layer	FastAPI
Vector Search	FAISS
Embeddings	nomic-embed-text
LLM	llama3.2
Visualization	HTML + JavaScript
Inference Runtime	Ollama
Installation
Clone Repository
git clone https://github.com/yourusername/vector-db-engine.git

cd vector-db-engine
Create Virtual Environment
python -m venv venv

source venv/bin/activate
Install Dependencies
pip install fastapi uvicorn pydantic numpy faiss-cpu ollama
Download Models
ollama pull nomic-embed-text

ollama pull llama3.2:1b
Run the Server
python main.py

Server:

http://127.0.0.1:8000
Example Workflow
Add Documents
Document
    ↓
Chunking
    ↓
Embedding
    ↓
FAISS Index
Ask Questions
Question
    ↓
Embedding
    ↓
Similarity Search
    ↓
Top-K Documents
    ↓
Llama 3.2
    ↓
Answer
Why FAISS?

FAISS was developed by Meta AI and is used for efficient similarity search over millions of vectors.

Advantages:

Optimized C++ backend
SIMD acceleration
Memory-efficient storage
Approximate nearest-neighbor retrieval

Without FAISS, search would require:

O(N)

comparisons per query.

With HNSW indexing:

O(log N)

average retrieval complexity.

Why HNSW?

Traditional structures such as KD-Trees degrade significantly in high-dimensional spaces.

HNSW solves this problem by constructing a navigable graph where vectors connect to their nearest neighbors.

Benefits:

Fast retrieval
Excellent recall
Scales to millions of vectors
Industry-standard ANN algorithm
Learning Outcomes

This project demonstrates practical understanding of:

Vector Databases
Embedding Models
Approximate Nearest Neighbor Search
HNSW Graphs
Retrieval-Augmented Generation
FastAPI Development
Local LLM Deployment
Semantic Search Systems