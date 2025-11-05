"""indexer.py
Index vectors into ChromaDB or FAISS. This is a starter example using chromadb.
"""
# Minimal example: implement real persistence and metadata handling in production
def create_index(vectors, metadatas, ids):
    # TODO: plug ChromaDB / FAISS here
    print("Index created with", len(vectors), "vectors")
