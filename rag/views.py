from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from core.responses import APIResponse
from core.mixins import AuthMixin
from .serializers import DocumentUploadSerializer
from .etl_pipeline import MockETLPipeline


class DocumentUploadView(AuthMixin, APIView):
    """API view for uploading and processing PDF files through ETL pipeline."""
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload and process PDF files through ETL pipeline."""
        serializer = DocumentUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return APIResponse.error(
                message="Invalid file upload",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            etl_processor = MockETLPipeline()
            uploaded_files = serializer.validated_data['files']
            
            # Process files through ETL pipeline
            results = etl_processor.process_multiple_files(uploaded_files)

            return APIResponse.success(
                message="PDF files processed successfully",
                data=results
            )
            
        except Exception as e:
            return APIResponse.error(
                message="Error processing PDF files",
                errors={'detail': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
