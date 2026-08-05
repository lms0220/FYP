from services.rag_service import create_vector_database


if __name__ == "__main__":
    result = create_vector_database()
    print(f"Created FAISS index from {result['documents']} documents and {result['chunks']} chunks.")
    print(f"Saved to: {result['index_path']}")
