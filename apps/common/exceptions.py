import logging

from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so every 4xx/5xx response emitted
    by the API is also logged with the view that raised it, instead of only
    showing up (or not) in Django's dev console.
    """
    response = drf_exception_handler(exc, context)
    view = context.get('view')

    if response is None:
        logger.exception("Unhandled exception in %s", view)
        return response

    if response.status_code >= 500:
        logger.error("%s in %s: %s", exc.__class__.__name__, view, response.data)
    elif response.status_code >= 400:
        logger.warning("%s in %s: %s", exc.__class__.__name__, view, response.data)

    return response
