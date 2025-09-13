from typing import List, Dict, Any
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings

from .models import Document, DocumentChunk
from .rag_engine import RAGEngine


class MockETLPipeline:
    """Mock ETL processor for PDF files - simulates document processing pipeline."""
    
    def __init__(self):
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP
        self.rag_engine = RAGEngine()
    
    def process_pdf_file(self, uploaded_file: UploadedFile) -> Dict[str, Any]:
        """Process a single PDF file and return mock extracted content."""
        # Mock PDF content extraction
        mock_content = self._extract_mock_content(uploaded_file.name)
        
        # Create document record
        document = Document.objects.create(
            title=uploaded_file.name,
            content=mock_content,
            metadata={
                'original_filename': uploaded_file.name,
                'processing_method': 'mock_etl',
                'extracted_at': '2024-01-01T00:00:00Z',
            }
        )
        
        # Process document into chunks
        chunks = self._create_document_chunks(document, mock_content)
        
        return {
            'status': 'success',
            'chunks_created': len(chunks),
            'message': 'Document processed successfully'
        }
    
    def process_multiple_files(self, uploaded_files: List[UploadedFile]) -> List[Dict[str, Any]]:
        """Process multiple PDF files."""
        results = []
        
        for uploaded_file in uploaded_files:
            try:
                result = self.process_pdf_file(uploaded_file)
                results.append(result)
            except Exception as e:
                results.append({
                    'status': 'error',
                    'filename': uploaded_file.name,
                    'error': str(e)
                })
        
        return results

    def _extract_mock_content(self, filename: str) -> str:
        """Extract mock content from PDF file."""
        # This is a mock implementation - in real scenario, you'd use PyPDF2, pdfplumber, etc.
        mock_contents = {
            'sample1.pdf': """
            Introduction to Machine Learning
            
            Machine learning is a subset of artificial intelligence that focuses on algorithms 
            that can learn from data. It has revolutionized many industries including healthcare, 
            finance, and technology.
            
            Types of Machine Learning:
            1. Supervised Learning: Learning with labeled data
            2. Unsupervised Learning: Finding patterns in unlabeled data
            3. Reinforcement Learning: Learning through interaction with environment
            
            Applications:
            - Image recognition and computer vision
            - Natural language processing
            - Recommendation systems
            - Predictive analytics
            """,
            'sample2.pdf': """
            Django Web Framework Guide
            
            Django is a high-level Python web framework that encourages rapid development 
            and clean, pragmatic design. It follows the Model-View-Template (MVT) pattern.
            
            Key Features:
            - Object-relational mapping (ORM)
            - Admin interface
            - URL routing
            - Template system
            - Security features
            
            Best Practices:
            - Use virtual environments
            - Follow PEP 8 coding standards
            - Write comprehensive tests
            - Use environment variables for configuration
            """,
            'sample3.pdf': """
            Database Design Principles
            
            Good database design is crucial for application performance and data integrity.
            
            Normalization Rules:
            1. First Normal Form (1NF): Eliminate duplicate columns
            2. Second Normal Form (2NF): Remove partial dependencies
            3. Third Normal Form (3NF): Remove transitive dependencies
            
            Indexing Strategies:
            - Primary keys for unique identification
            - Foreign keys for relationships
            - Composite indexes for multi-column queries
            - Partial indexes for filtered queries
            """
        }
        
        # Return mock content based on filename or default content
        return mock_contents.get(filename, f"""
        Document: {filename}
        
        This is a mock document content for demonstration purposes.
        In a real implementation, this would contain the actual extracted
        text content from the PDF file.
        
        Key topics covered:
        - Document processing
        - Text extraction
        - Content analysis
        - Data indexing
        
        This mock content is used to demonstrate the RAG pipeline
        functionality without requiring actual PDF processing libraries.
        """)
    
    def _create_document_chunks(self, document: Document, content: str) -> List[DocumentChunk]:
        """Split document content into chunks and create embeddings."""
        chunks = []
        
        # Simple text chunking (in real implementation, use more sophisticated chunking)
        text_chunks = self._split_text_into_chunks(content)
        
        # Generate embeddings for all chunks at once
        embeddings = self.rag_engine.create_embeddings(text_chunks)
        
        for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
            # Create document chunk
            chunk = DocumentChunk.objects.create(
                document=document,
                content=chunk_text,
                embedding=embedding,
                metadata={
                    'chunk_index': i,
                    'chunk_method': 'simple_split',
                    'chunk_size': len(chunk_text),
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        
        if len(words) <= self.chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(words):
                break
        
        return chunks
