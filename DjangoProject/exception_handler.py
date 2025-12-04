"""
Custom exception handler for Django REST Framework.
Prevents stack trace exposure in API responses.
"""
from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Prevents stack trace exposure in API responses.
    
    Returns generic error responses without stack traces or sensitive information.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Always sanitize response data to prevent stack trace exposure
        # This applies to both DEBUG=True and DEBUG=False
        
        # Map status codes to appropriate error messages
        if response.status_code == 404:
            error_response = {
                'error': 'Not found',
                'detail': 'The requested resource was not found.'
            }
        elif response.status_code == 403:
            error_response = {
                'error': 'Forbidden',
                'detail': 'You do not have permission to access this resource.'
            }
        elif response.status_code == 400:
            error_response = {
                'error': 'Bad request',
                'detail': 'The request was malformed or invalid.'
            }
        elif response.status_code >= 500:
            # Production: return generic error
            if not settings.DEBUG:
                error_response = {
                    'error': 'Internal server error',
                    'detail': 'An error occurred while processing your request.'
                }
            else:
                # Development: show error but no stack trace
                error_response = {
                    'error': 'Internal server error',
                    'detail': 'An error occurred. Check server logs for details.'
                }
        else:
            # Other status codes: use generic message
            error_response = {
                'error': 'An error occurred',
                'detail': 'The request could not be processed.'
            }
        
        response.data = error_response
    
    # Handle unhandled exceptions (500 errors that DRF doesn't catch)
    elif response is None:
        # Unhandled exception occurred (e.g., database errors)
        # Always return generic error, never expose stack trace
        if not settings.DEBUG:
            # Production: return generic error
            error_response = {
                'error': 'Internal server error',
                'detail': 'An error occurred while processing your request.'
            }
        else:
            # Development: still hide stack trace but indicate error
            error_response = {
                'error': 'Internal server error',
                'detail': 'An error occurred. Check server logs for details.'
            }
        
        response = Response(error_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response

