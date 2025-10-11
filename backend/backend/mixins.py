from rest_framework import status
from rest_framework.response import Response

def http_method_mixin(request, *args, **kwargs):
    """Disallow PUT operation."""
    if request.method == "PUT":
        return Response(
            {"error": "PUT operation not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    return None
