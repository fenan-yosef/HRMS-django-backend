import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

# Get an instance of a logger
logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler that logs the exception and returns a generic error message.
    """
    # Log the exception
    logger.exception(exc)  # Logs the exception with traceback

    # Let DRF build the standard error response first
    response = exception_handler(exc, context)
    if response is not None:
        # Wrap the existing error details with a generic message
        response.data = {"errors": {"detail": "A server error occurred."}}
    else:
        # Fallback for non-DRF exceptions
        return Response(
            {"errors": {"detail": "Internal server error."}},
            status=500
        )
    return response
