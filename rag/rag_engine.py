import numpy as np
from typing import List, Optional
from django.conf import settings
from pgvector.django import CosineDistance
import openai
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure we have a handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

from .models import DocumentChunk


class RAGEngine:
    """RAG Engine for document retrieval and context building."""
    
    def __init__(self):
        self.embedding_model = settings.RAG_EMBEDDING_MODEL
        self.vector_dimension = settings.RAG_VECTOR_DIMENSION
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP
        self.max_context_tokens = settings.RAG_MAX_CONTEXT_TOKENS
        self.top_k_results = settings.RAG_TOP_K_RESULTS
        self.similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD
        
        if settings.OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
    
    def create_embedding(self, text_chunk: str) -> List[float]:
        """Create embedding for a single text chunk using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text_chunk
        )
        return response.data[0].embedding

    def create_batch_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        """Create embeddings for text chunks using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        embeddings = []
        for chunk in text_chunks:
            try:
                response = self.create_embedding(chunk)

                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"Error generating embedding: {e}")
                embeddings.append([0.1] * self.vector_dimension)
        
        return embeddings
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[DocumentChunk]:
        """Retrieve top_k chunks using cosine similarity."""
        logging.info(f"Retrieving chunks for query: {query}")
        print(f"[RAG_ENGINE] Retrieving chunks for query: {query}")
        
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        if top_k is None:
            top_k = self.top_k_results
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            logging.info(f"Response: {response}")
            print(f"[RAG_ENGINE] OpenAI response received")
            query_embedding = np.array(response.data[0].embedding)
            logging.info(f"Query embedding: {query_embedding}")
            print(f"[RAG_ENGINE] Query embedding created, shape: {query_embedding.shape}")
        except Exception as e:
            logging.info(f"Error generating query embedding: {e}")
            print(f"[RAG_ENGINE] Error generating query embedding: {e}")
            return []
        
        logging.info(f"Retrieving chunks")
        print(f"[RAG_ENGINE] Starting database query for chunks")

        try:
            chunks = DocumentChunk.objects.annotate(
                similarity=1 - CosineDistance('embedding', query_embedding)
            ).filter(
                similarity__gte=self.similarity_threshold
            ).order_by('-similarity')[:top_k]
            
            chunks_list = list(chunks)
            logging.info(f"Retrieved {len(chunks_list)} chunks from database")
            print(f"[RAG_ENGINE] Retrieved {len(chunks_list)} chunks from database")
            return chunks_list
        except Exception as e:
            logging.info(f"Error retrieving chunks qs: {e}")
            print(f"[RAG_ENGINE] Error retrieving chunks qs: {e}")
            return []
    
    def build_context(
        self,
        chunks: List[DocumentChunk],
        max_tokens: Optional[int] = None
    ) -> str:
        """Build context string from retrieved chunks."""
        logging.info(f"Building context from {len(chunks)} chunks")
        print(f"[RAG_ENGINE] Building context from {len(chunks)} chunks")
        
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        context_parts = []
        current_tokens = 0
        
        for i, chunk in enumerate(chunks):
            chunk_tokens = len(chunk.content) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                logging.info(f"Stopping at chunk {i} due to token limit")
                print(f"[RAG_ENGINE] Stopping at chunk {i} due to token limit")
                break
            
            context_part = f"{chunk.content}\n"
            context_parts.append(context_part)
            current_tokens += chunk_tokens
        
        final_context = "\n".join(context_parts)
        logging.info(f"Built context with {len(final_context)} characters from {len(context_parts)} chunks")
        print(f"[RAG_ENGINE] Built context with {len(final_context)} characters from {len(context_parts)} chunks")
        return final_context
    
    def retrieve_and_build_context(self, query: str, top_k: Optional[int] = None) -> str:
        """Convenience method to retrieve chunks and build context in one call."""
        logging.info(f"Retrieving chunks and building context for query: {query}")

        chunks = self.retrieve(query, top_k)
        logging.info(f"Chunks: {chunks}")

        return self.build_context(chunks)
