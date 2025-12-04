"""
Custom error handlers for Django project.
Prevents stack trace exposure in production.
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings


def handler404(request, exception):
    """
    Custom 404 error handler.
    Prevents stack trace exposure.
    """
    if request.path.startswith('/api/'):
        # API endpoints return JSON
        return JsonResponse({
            'error': 'Not found',
            'detail': 'The requested resource was not found.'
        }, status=404)
    
    # Web pages return HTML (if templates exist)
    context = {'error_code': 404, 'error_message': 'Page not found'}
    return render(request, 'errors/404.html', context, status=404)


def handler500(request):
    """
    Custom 500 error handler.
    Prevents stack trace exposure.
    """
    if request.path.startswith('/api/'):
        # API endpoints return JSON
        return JsonResponse({
            'error': 'Internal server error',
            'detail': 'An error occurred while processing your request.'
        }, status=500)
    
    # Web pages return HTML (if templates exist)
    context = {'error_code': 500, 'error_message': 'Internal server error'}
    return render(request, 'errors/500.html', context, status=500)


def handler403(request, exception):
    """
    Custom 403 error handler.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Forbidden',
            'detail': 'You do not have permission to access this resource.'
        }, status=403)
    
    context = {'error_code': 403, 'error_message': 'Forbidden'}
    return render(request, 'errors/403.html', context, status=403)


def handler400(request, exception):
    """
    Custom 400 error handler.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Bad request',
            'detail': 'The request was malformed.'
        }, status=400)
    
    context = {'error_code': 400, 'error_message': 'Bad request'}
    return render(request, 'errors/400.html', context, status=400)

