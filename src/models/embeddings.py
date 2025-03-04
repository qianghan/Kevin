import numpy as np
import logging
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

class SimpleEmbeddings(Embeddings):
    """
    A simple embedding class that creates deterministic embeddings based on text content.
    This is used for testing purposes when more complex embedding models are not available.
    """
    def __init__(self, dimension=10):
        """
        Initialize the SimpleEmbeddings class.
        
        Args:
            dimension: Dimension of the embeddings (default: 10)
        """
        self.dimension = dimension
        logger.info(f"Initialized SimpleEmbeddings with dimension {dimension}")
    
    def embed_documents(self, texts):
        """
        Create embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        # Create deterministic embeddings based on the text content
        # This ensures the same text always gets the same embedding
        embeddings = []
        for text in texts:
            # Create a seed from the hash of the text
            seed = hash(text) % 10000
            np.random.seed(seed)
            # Create an embedding with the specified dimension
            embeddings.append(np.random.rand(self.dimension).astype(np.float32))
        return embeddings
    
    def embed_query(self, text):
        """
        Create an embedding for a query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding for the query
        """
        # Create a deterministic embedding for a query
        seed = hash(text) % 10000
        np.random.seed(seed)
        return np.random.rand(self.dimension).astype(np.float32) 