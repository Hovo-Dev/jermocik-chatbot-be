from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from .responses import APIResponse


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""
    
    def get(self, request):
        """Return basic health status."""
        return APIResponse.success({
            "status": "healthy",
            "service": "django-api-boilerplate"
        })


class ReadinessCheckView(APIView):
    """Readiness check endpoint for Kubernetes."""
    
    def get(self, request):
        """Check if the service is ready to accept traffic."""
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Check cache connection
            cache.set('health_check', 'ok', 10)
            cache.get('health_check')
            
            return APIResponse.success({
                "status": "ready",
                "database": "connected",
                "cache": "connected"
            })
        except Exception as e:
            return APIResponse.error(
                f"Service not ready: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class LivenessCheckView(APIView):
    """Liveness check endpoint for Kubernetes."""
    
    def get(self, request):
        """Check if the service is alive."""
        return APIResponse.success({
            "status": "alive",
            "service": "django-api-boilerplate"
        })
