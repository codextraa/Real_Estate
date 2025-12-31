from rest_framework import status
from rest_framework.response import Response


def http_method_mixin(request, *args, **kwargs):
    """Disallow PUT and PATCH operation."""
    if request.method in ('PUT', 'PATCH'):
        return Response(
            {"error": "PUT or PATCH operation not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    return None
