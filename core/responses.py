from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """Simple API response helper class."""
    
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """Return a successful response."""
        response_data = {
            "success": True,
            "message": message,
        }
        if data is not None:
            response_data["data"] = data
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message="Error", errors=None, error_code=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Return an error response with detailed error information."""
        response_data = {
            "success": False,
            "message": message,
        }
        
        if errors is not None:
            response_data["errors"] = errors
            
        if error_code is not None:
            response_data["error_code"] = error_code
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(data=None, message="Created successfully"):
        """Return a created response."""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)
