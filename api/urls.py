"""
URL configuration for API app.

This module defines RESTful API endpoints for external clients
to interact with the forum system using JSON format.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet, basename='thread')
router.register(r'replies', views.ReplyViewSet, basename='reply')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    # Include router URLs for ViewSets
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('auth/whoami/', views.WhoAmIAPIView.as_view(), name='api_whoami'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('auth/verify-otp/', views.VerifyOTPAPIView.as_view(), name='api_verify_otp'),
    path('auth/resend-otp/', views.ResendOTPAPIView.as_view(), name='api_resend_otp'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('auth/register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('auth/toggle-anonymous/', views.ToggleAnonymousModeAPIView.as_view(), name='api_toggle_anonymous'),
    path('threads/<int:thread_id>/replies/', views.ThreadRepliesAPIView.as_view(), name='thread_replies'),
    path('threads/<int:thread_id>/like/', views.ThreadLikeAPIView.as_view(), name='thread_like'),
    path('replies/<int:reply_id>/like/', views.ReplyLikeAPIView.as_view(), name='reply_like'),
    path('search/', views.SearchAPIView.as_view(), name='api_search'),
]
