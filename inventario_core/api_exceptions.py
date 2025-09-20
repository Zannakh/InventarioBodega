from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Formatea Django ValidationError como 400 limpio en toda la API.
    Delega el resto al handler por defecto de DRF.
    """
    if isinstance(exc, DjangoValidationError):
        return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    response = exception_handler(exc, context)
    return response
