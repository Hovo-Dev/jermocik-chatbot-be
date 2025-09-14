from django.urls import path
from . import views

app_name = 'rag'

urlpatterns = [
    # Document Structured Ingestion
    path('documents/ingest/structured/', views.DocumentIngestView.as_view(), name='document-upload'),
    # Document Unstructured Ingestion
    path('documents/ingest/graphrag/', views.GraphRAGSetupView.as_view(), name='graphrag-setup'),
]
