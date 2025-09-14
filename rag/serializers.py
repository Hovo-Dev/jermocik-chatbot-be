from rest_framework import serializers

class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload endpoint."""
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        max_length=10,
        help_text="List of PDF files to upload and process"
    )
    
    def validate_files(self, value):
        """Validate uploaded files."""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 files allowed per upload")
        
        for file in value:
            if not file.name.lower().endswith('.pdf'):
                raise serializers.ValidationError(f"File {file.name} is not a PDF")
        
        return value
