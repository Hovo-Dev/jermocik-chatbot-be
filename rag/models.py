from django.db import models
from pgvector.django import VectorField
from django.conf import settings


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Document(BaseModel):
    """Document model for storing PDF metadata and content."""
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'rag_documents'
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class DocumentChunk(BaseModel):
    """Document chunk with embedding for vector similarity search."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks', null=True, blank=True)
    content = models.TextField()
    summary = models.TextField(default="", blank=True)
    embedding = VectorField(dimensions=settings.RAG_VECTOR_DIMENSION)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'rag_document_chunks'
        indexes = [
            models.Index(fields=['document']),
        ]

    def __str__(self):
        document_title = self.document.title if self.document else "No Document"

        return f"{document_title} - Content {self.content}"
