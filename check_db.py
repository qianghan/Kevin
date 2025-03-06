import sys
import os
from pathlib import Path
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path to import the modules
sys.path.append('.')

try:
    # Import required modules from langchain
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document
    import faiss

    print(f"Checking database contents...")

    # Path to the vectordb
    vectordb_path = Path("data/vectordb")
    
    # Check if the files exist
    index_files = ["index.faiss", "index.pkl"]
    for file in index_files:
        file_path = vectordb_path / file
        if file_path.exists():
            print(f"File {file} exists: {file_path.exists()}")
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            print(f"  Size: {file_size_mb:.2f} MB")
        else:
            print(f"File {file} does not exist!")
    
    # Load the embedding function
    try:
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        print(f"Embedding function loaded successfully")
    except Exception as e:
        print(f"Error loading embedding function: {e}")
        sys.exit(1)
    
    # Load the FAISS index
    try:
        vectordb = FAISS.load_local(
            vectordb_path,
            embedding_function,
            allow_dangerous_deserialization=True
        )
        print(f"Vector database loaded successfully")
        
        # Get the document count
        docs = vectordb.docstore._dict
        print(f"Number of documents: {len(docs)}")
        
        # Access the first few document IDs
        if docs:
            doc_ids = list(docs.keys())[:3]
            print(f"\nSample document IDs: {doc_ids}")
            
            # Try to access documents directly by ID
            print("\nDirect document access test:")
            for doc_id in doc_ids:
                try:
                    doc = docs[doc_id]
                    print(f"Document with ID {doc_id} retrieved successfully.")
                    print(f"Content (first 150 chars): {doc.page_content[:150]}...")
                except Exception as e:
                    print(f"Error retrieving document with ID {doc_id}: {e}")
        
        # Try a similarity search using the raw embedding
        print("\nTrying raw similarity search:")
        try:
            # Create an embedding for a test query
            test_query = "Carleton University admissions"
            print(f"Query: {test_query}")
            test_embedding = embedding_function.embed_query(test_query)
            
            # Access the raw FAISS index
            faiss_index = vectordb.index
            
            # Search the index directly
            D, I = faiss_index.search(np.array([test_embedding]), k=5)
            print(f"Raw FAISS search results:")
            print(f"Distances: {D}")
            print(f"Indices: {I}")
            
            # Try to retrieve the documents using the indices
            if I.size > 0 and I[0].size > 0:
                print("\nTrying to retrieve documents using indices:")
                for idx in I[0]:
                    if idx < len(vectordb.index_to_docstore_id):
                        doc_id = vectordb.index_to_docstore_id[idx]
                        print(f"Index {idx} maps to document ID: {doc_id}")
                        if doc_id in docs:
                            doc = docs[doc_id]
                            print(f"  Content (first 100 chars): {doc.page_content[:100]}...")
                        else:
                            print(f"  Document ID {doc_id} not found in docstore.")
                    else:
                        print(f"Index {idx} is out of bounds (max: {len(vectordb.index_to_docstore_id)-1})")
            else:
                print("No indices returned from search.")
            
        except Exception as e:
            print(f"Error during raw FAISS search: {e}")
                
    except Exception as e:
        print(f"Error loading vector database: {e}")
        
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed the required packages:"+
          "\npip install langchain-huggingface langchain-community sentence-transformers") 