import numpy as np
import logging
from langchain_core.embeddings import Embeddings
import hashlib
from typing import List

logger = logging.getLogger(__name__)

class SimpleEmbeddings(Embeddings):
    """
    A simple embedding class that creates deterministic embeddings based on text content.
    This is used for testing purposes when more complex embedding models are not available.
    """
    def __init__(self, dimension=384):  # Increased dimension for better representation
        """
        Initialize the SimpleEmbeddings class.
        
        Args:
            dimension: Dimension of the embeddings (default: 384)
        """
        self.dimension = dimension
        logger.info(f"Initialized SimpleEmbeddings with dimension {dimension}")
    
    def _create_embedding(self, text: str) -> np.ndarray:
        """
        Create a deterministic embedding for a text.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Embedding vector
        """
        # Create a more robust hash of the text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Use the hash to create a deterministic seed
        seed = int(text_hash[:8], 16) % 10000
        
        # Set random seed for reproducibility
        np.random.seed(seed)
        
        # Create embedding with better distribution
        embedding = np.random.normal(0, 1, self.dimension)
        # Normalize the embedding
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.astype(np.float32)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        logger.debug(f"Creating embeddings for {len(texts)} documents")
        
        try:
            embeddings = [self._create_embedding(text).tolist() for text in texts]
            logger.debug(f"Successfully created {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error creating document embeddings: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Create an embedding for a query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding for the query
        """
        logger.debug(f"Creating embedding for query: {text[:50]}...")
        
        try:
            embedding = self._create_embedding(text).tolist()
            logger.debug("Successfully created query embedding")
            return embedding
        except Exception as e:
            logger.error(f"Error creating query embedding: {e}")
            raise 