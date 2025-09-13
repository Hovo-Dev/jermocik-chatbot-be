from django.urls import path
from . import views

app_name = 'rag'

urlpatterns = [
    # Document Ingestion
    path('documents/ingest/structured/', views.DocumentUploadView.as_view(), name='document-upload'),
]
