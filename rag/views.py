import asyncio
from pathlib import Path
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from core.responses import APIResponse
from core.mixins import AuthMixin
from etl.processors.pipeline import ETLPipeline
from rag.graphrag_client import GraphRAGClient

class DocumentIngestView(AuthMixin, APIView):
    """API view for uploading and processing PDF files through ETL pipeline."""
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload and process PDF files through ETL pipeline."""
        try:
            # Create etl/input directory if it doesn't exist
            input_dir = Path('etl/input')
            output_dir = Path('etl/results')

            # Initialize pipeline with the saved files directory
            pipeline = ETLPipeline(input_dir, output_dir)

            # Run the ETL pipeline
            pipeline.run()

            return APIResponse.success(
                message="PDF files processed successfully",
            )
            
        except Exception as e:
            return APIResponse.error(
                message="Error processing PDF files",
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GraphRAGSetupView(APIView):
    """API view for testing GraphRAG connection, ingesting documents, and creating indexes."""
    
    def post(self, request):
        """Test connection, ingest documents, and create indexes."""
        try:
            # Initialize GraphRAG client
            client = GraphRAGClient()
            
            # Test connection
            if not client.test_connection():
                return APIResponse.error(
                    message="GraphRAG connection test failed",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get PDF files from etl/input directory
            input_dir = Path('etl/input')
            pdf_files = []
            
            if input_dir.exists():
                pdf_files = [str(pdf_file) for pdf_file in input_dir.glob('*.pdf')]
            
            if not pdf_files:
                return APIResponse.error(
                    message="No PDF files found in etl/input directory",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            # Ingest documents using synchronous wrapper
            client.ingest_documents_sync(pdf_files)
            
            # Create indexes
            client.create_indexes()
            
            # Close client connection
            client.close()
            
            return APIResponse.success(
                message="GraphRAG setup document ingestion completed successfully",
            )
            
        except Exception as e:
            return APIResponse.error(
                message="Error during GraphRAG setup document ingestion",
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
