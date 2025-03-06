# Test script for RAG engine
from src.rag.engine import RAGEngine
import os
import sys

def test_rag():
    print("Testing RAG engine...")
    config_path = 'config.yaml'
    print(f"Using config file: {config_path}")
    
    try:
        engine = RAGEngine(config_path)
        print('Vector database loaded successfully:', engine.has_vectordb)
        
        if engine.has_vectordb:
            # Debug information
            print("\nDEBUG: Vector Database Information")
            if hasattr(engine.vectordb, '_collection'):
                print(f"Collection size: {len(engine.vectordb._collection)}")
            elif hasattr(engine.vectordb, 'index'):
                print(f"Index contains vectors: {engine.vectordb.index is not None}")
                if hasattr(engine.vectordb, 'docstore') and engine.vectordb.docstore:
                    print(f"Document store has {len(engine.vectordb.docstore._dict)} documents")
            
            # Try a few different queries
            test_queries = [
                "university",
                "canada",
                "education",
                "admission",
                "What is the University of Toronto known for?",
                "What are the admission requirements for undergraduate programs?"
            ]
            
            for query in test_queries:
                print(f"\nTesting query: '{query}'")
                docs = engine.retrieve_documents(query)
                print(f"Retrieved {len(docs)} documents")
                
                if docs:
                    print("\nFirst document preview:")
                    print(f"Source: {docs[0].metadata.get('source', 'Unknown')}")
                    print(f"Content preview: {docs[0].page_content[:150]}...")
                
                result = engine.process_query(query)
                print(f"\nQuery result summary: {'Found information' if 'No relevant information' not in result else 'No information found'}")
        else:
            print("Vector database not available. Test failed.")
    
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag() 