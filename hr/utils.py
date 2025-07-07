from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    # Let DRF build the standard error response first
    response = exception_handler(exc, context)
    if response is not None:
        # Wrap the existing error details
        response.data = { "errors": response.data }
    else:
        # Fallback for non‐DRF exceptions
        return Response(
            { "errors": { "detail": "Internal server error." } },
            status=500
        )
    return response
