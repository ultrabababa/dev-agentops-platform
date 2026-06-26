# Use Lightweight Hybrid Retrieval Before a Vector Database

V1 will implement retrieval as a lightweight hybrid capability: keyword or BM25-style search for logs, embedding similarity for documentation, and path, symbol, or keyword search for repository files. A dedicated vector database such as pgvector, Qdrant, Milvus, or Weaviate is deferred until the curated case set and evidence hit rate show that retrieval quality, scale, filtering, or service operation requires it.
