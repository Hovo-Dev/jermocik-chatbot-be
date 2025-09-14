from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    list_display = ['title', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin interface for DocumentChunk model."""
    list_display = ['document', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'document__title']
    readonly_fields = ['embedding', 'created_at', 'updated_at']
    ordering = ['document__title']
