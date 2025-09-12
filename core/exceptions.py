from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler to standardize error responses.

    :param exc: The exception instance raised during the view's execution.
    :param context: Context information about the exception, including view and request.
    :return: Modified DRF response with standardized error structure.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize error response format
        if isinstance(exc, ValidationError):
            # Handle validation errors with detailed field information
            errors = {}
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    errors[field] = messages
                else:
                    errors[field] = [str(messages)]

            response.data = {
                "success": False,
                "message": "Validation failed",
                "errors": errors,
                "error_code": "VALIDATION_ERROR"
            }
        else:
            # Handle other exceptions
            error_message = str(exc) if hasattr(exc, '__str__') else "An error occurred"
            response.data = {
                "success": False,
                "message": error_message,
                "error_code": exc.__class__.__name__.upper()
            }

    return response
