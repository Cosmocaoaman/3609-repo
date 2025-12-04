"""
API views for RESTful endpoints.

This module provides RESTful API endpoints for external clients
to interact with the forum system using JSON format.
"""
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission


class IsCustomAdminUser(BasePermission):
    """Custom permission to only allow admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   (request.user.is_admin or request.user.is_staff or request.user.is_superuser))
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.filters import OrderingFilter, SearchFilter
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.core.mail import send_mail
from forum.email_service import email_service
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from forum.models import User, Thread, Reply, Tag, Category, ThreadLike, ReplyLike, ThreadTags, ThreadView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .serializers import (
    UserSerializer, ThreadSerializer, ReplySerializer, TagSerializer, TagCreateSerializer,
    CategorySerializer, ThreadLikeSerializer, ReplyLikeSerializer,
    ThreadListSerializer
)
import json
# from forum.models import Thread, Reply, Tag, Category, ThreadLike, ReplyLike


class WhoAmIAPIView(APIView):
    """
    Return current session/auth status for the frontend to restore state.
    GET /api/auth/whoami/
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            is_admin_user = getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
            # Admin users should always appear as non-anonymous for UI purposes
            return Response({
                'logged_in': True,
                'user_id': user.id,
                'username': user.username,
                'is_anonymous': False if is_admin_user else getattr(user, 'is_anonymous', False),
                'is_staff': getattr(user, 'is_staff', False),
                'is_superuser': getattr(user, 'is_superuser', False),
                'is_admin': getattr(user, 'is_admin', False),
            })
        return Response({'logged_in': False})

class ThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Thread CRUD operations.
    
    Provides RESTful endpoints for:
    - GET /api/threads/ - List all threads (with pagination and sorting)
    - POST /api/threads/ - Create new thread
    - GET /api/threads/{id}/ - Retrieve specific thread
    - PUT /api/threads/{id}/ - Update thread
    - DELETE /api/threads/{id}/ - Delete thread
    
    Query parameters:
    - ordering: Sort by field (e.g., ?ordering=-create_time, ?ordering=title)
    - search: Search in title and body (e.g., ?search=django)
    """
    queryset = Thread.objects.all().order_by('-create_time')
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['create_time', 'edit_time', 'title']
    ordering = ['-create_time']
    search_fields = ['title', 'body']
    
    def get_serializer_class(self):
        """Use different serializers for list vs detail views."""
        if self.action == 'list':
            return ThreadListSerializer
        return ThreadSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context for admin checking."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Optionally include deleted when requested by admin users."""
        include_deleted = self.request.query_params.get('include_deleted')
        tag_param = self.request.query_params.get('tag')
        category_param = self.request.query_params.get('category')
        ids_param = self.request.query_params.get('ids')  # Handle ids parameter for search filtering
        base_qs = super().get_queryset()
        user = getattr(self.request, 'user', None)
        is_admin_user = bool(user) and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False))
        
        # Handle ids filtering (for search results)
        if ids_param:
            try:
                thread_ids = [int(id.strip()) for id in ids_param.split(',') if id.strip()]
                if thread_ids:
                    base_qs = base_qs.filter(id__in=thread_ids)
            except (ValueError, TypeError):
                pass  # Invalid ids, ignore filter
        
        # Handle tag filtering
        if tag_param:
            # support single or comma-separated tag names
            tag_names = [t.strip() for t in tag_param.split(',') if t.strip()]
            if tag_names:
                # First check if all tags exist
                from forum.models import Tag
                existing_tags = Tag.objects.filter(name__in=tag_names, is_active=True).values_list('name', flat=True)
                
                # Only apply filter if at least one tag exists
                if len(existing_tags) > 0:
                    # Use OR logic: thread must contain ANY of the specified tags
                    base_qs = base_qs.filter(threadtags__tag_id__name__in=existing_tags).distinct()
                else:
                    # If no tags exist, return empty queryset
                    base_qs = base_qs.none()
        
        # Handle category filtering
        if category_param:
            try:
                category_id = int(category_param)
                base_qs = base_qs.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass  # Invalid category ID, ignore filter
        
        # Handle deleted threads
        if include_deleted and include_deleted.lower() == 'true' and is_admin_user:
            return base_qs
        return base_qs.filter(is_deleted=False)
    
    def perform_create(self, serializer):
        """Set the author when creating a new thread."""
        serializer.save(user_id=self.request.user)
    
    def perform_update(self, serializer):
        """Update edit_time when modifying thread."""
        serializer.save()
    
    def get_object(self):
        """Get object with permission check for update/delete."""
        obj = super().get_object()
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only authors can edit or delete their own threads
            if obj.user_id != self.request.user:
                # Allow admins to manage any thread
                user = self.request.user
                is_admin_user = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False)
                if not is_admin_user:
                    raise PermissionDenied("You can only edit or delete your own threads")
        return obj
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete thread"""
        # Fetch regardless of is_deleted filter
        try:
            instance = Thread.objects.get(pk=kwargs.get('pk'))
        except Thread.DoesNotExist:
            return Response({'error': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        # Permission: author or admin
        user = request.user
        is_admin_user = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False)
        if instance.user_id != user and not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit or delete your own threads")
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def restore(self, request, pk=None):
        """Restore a soft deleted thread (admin only)."""
        try:
            thread = Thread.objects.get(pk=pk)
        except Thread.DoesNotExist:
            return Response({'error': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is banned - don't restore threads from banned users
        if thread.user_id.is_banned:
            return Response({
                'error': 'Cannot restore thread from banned user. Unban the user first.',
                'user_banned': True,
                'user_id': thread.user_id.id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        thread.restore()
        return Response({
            'success': True,
            'thread_id': thread.id,
            'is_deleted': thread.is_deleted,
            'message': 'Thread restored successfully'
        })
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get all replies for a specific thread."""
        thread = self.get_object()
        replies = Reply.objects.filter(thread_id=thread, is_deleted=False).order_by('create_time')
        serializer = ReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def viewed(self, request, pk=None):
        """Record that current user viewed this thread. Upsert latest timestamp."""
        thread = self.get_object()
        # Only for authenticated users; anonymous can be ignored or extended later
        if not request.user or not request.user.is_authenticated:
            return Response({'ignored': True}, status=status.HTTP_200_OK)
        ThreadView.objects.update_or_create(
            user_id=request.user,
            thread_id=thread,
            defaults={'viewed_at': timezone.now()}
        )
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like status for a thread."""
        thread = self.get_object()
        like, created = ThreadLike.objects.get_or_create(
            user_id=request.user, thread_id=thread
        )
        if not created:
            like.status = not like.status
            like.save()
        else:
            like.status = True
            like.save()
        
        return Response({
            'liked': like.status,
            'like_count': ThreadLike.objects.filter(thread_id=thread, status=True).count()
        })
    


class ReplyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reply CRUD operations.
    
    Provides RESTful endpoints for:
    - GET /api/replies/ - List all replies (with pagination and sorting)
    - POST /api/replies/ - Create new reply
    - GET /api/replies/{id}/ - Retrieve specific reply
    - PUT /api/replies/{id}/ - Update reply
    - DELETE /api/replies/{id}/ - Delete reply
    
    Query parameters:
    - ordering: Sort by field (e.g., ?ordering=-create_time, ?ordering=create_time)
    - search: Search in body content (e.g., ?search=help)
    """
    queryset = Reply.objects.all().order_by('-create_time')
    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['create_time', 'edit_time']
    ordering = ['-create_time']
    search_fields = ['body']
    
    def get_serializer_context(self):
        """Add request to serializer context for admin checking."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """Optionally include deleted when requested by admin users."""
        include_deleted = self.request.query_params.get('include_deleted')
        base_qs = super().get_queryset()
        user = getattr(self.request, 'user', None)
        is_admin_user = bool(user) and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False))
        
        if include_deleted and include_deleted.lower() == 'true' and is_admin_user:
            return base_qs
        return base_qs.filter(is_deleted=False)
    
    def perform_create(self, serializer):
        """Set the author when creating a new reply."""
        serializer.save(user_id=self.request.user)
    
    def perform_update(self, serializer):
        """Update edit_time when modifying reply."""
        serializer.save()
    
    def get_object(self):
        """Get object with permission check for update/delete."""
        obj = super().get_object()
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only authors can edit or delete their own replies
            if obj.user_id != self.request.user:
                # Allow admins to manage any reply
                user = self.request.user
                is_admin_user = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False)
                if not is_admin_user:
                
                    raise PermissionDenied("You can only edit or delete your own replies")
        return obj
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete reply"""
        try:
            instance = Reply.objects.get(pk=kwargs.get('pk'))
        except Reply.DoesNotExist:
            return Response({'error': 'Reply not found'}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        is_admin_user = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False)
        if instance.user_id != user and not is_admin_user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit or delete your own replies")
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def restore(self, request, pk=None):
        """Restore a soft-deleted reply (admin only)."""
        try:
            instance = Reply.objects.get(pk=pk)
        except Reply.DoesNotExist:
            return Response({'error': 'Reply not found'}, status=status.HTTP_404_NOT_FOUND)
        instance.restore()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like status for a reply."""
        reply = self.get_object()
        like, created = ReplyLike.objects.get_or_create(
            user_id=request.user, reply_id=reply
        )
        if not created:
            like.status = not like.status
            like.save()
        else:
            like.status = True
            like.save()
        
        return Response({
            'liked': like.status,
            'like_count': ReplyLike.objects.filter(reply_id=reply, status=True).count()
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User read operations.
    
    Provides read-only endpoints for:
    - GET /api/users/ - List all users
    - GET /api/users/{id}/ - Retrieve specific user
    
    Query parameters:
    - search: Search in username and email (e.g., ?search=john)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'email']

    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """Update current user's username and bio with validation."""
        user = request.user
        username = request.data.get('username')
        bio = request.data.get('bio')

        # Validate username
        if username is not None:
            username = str(username).strip()
            if len(username) == 0:
                return Response({'error': 'Username cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
            if len(username) > 50:
                return Response({'error': 'Username too long (max 50)'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if username already exists (excluding current user)
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate bio
        if bio is not None:
            bio = str(bio).strip()
            if len(bio) > 300:
                return Response({'error': 'Bio too long (max 300)'}, status=status.HTTP_400_BAD_REQUEST)

        # Save
        if username is not None:
            user.username = username
        if bio is not None:
            user.bio = bio
        user.save()
        return Response({'success': True, 'username': user.username, 'bio': user.bio})

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Return aggregate statistics for a specific user."""
        try:
            target_user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Posts and replies created by user (excluding soft-deleted)
        thread_count = Thread.objects.filter(user_id=target_user, is_deleted=False).count()
        reply_count = Reply.objects.filter(user_id=target_user, is_deleted=False).count()

        # Likes given by this user
        given_thread_likes = ThreadLike.objects.filter(user_id=target_user, status=True).count()
        given_reply_likes = ReplyLike.objects.filter(user_id=target_user, status=True).count()

        # Likes received on user's content
        received_thread_likes = ThreadLike.objects.filter(thread_id__user_id=target_user, status=True).count()
        received_reply_likes = ReplyLike.objects.filter(reply_id__user_id=target_user, status=True).count()

        return Response({
            'user_id': target_user.id,
            'username': target_user.username,
            'bio': getattr(target_user, 'bio', None),
            'thread_count': thread_count,
            'reply_count': reply_count,
            'given_likes': {
                'threads': given_thread_likes,
                'replies': given_reply_likes,
                'total': given_thread_likes + given_reply_likes,
            },
            'received_likes': {
                'threads': received_thread_likes,
                'replies': received_reply_likes,
                'total': received_thread_likes + received_reply_likes,
            },
        })

    @action(detail=True, methods=['get', 'delete'])
    def history(self, request, pk=None):
        """
        GET: return browsing history (10 per page) sorted by viewed_at desc; dedup ensured by model uniqueness.
        DELETE: clear history for this user.
        """
        try:
            target_user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            if request.user != target_user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Cannot clear history of another user')
            ThreadView.objects.filter(user_id=target_user).delete()
            return Response({'success': True})

        # GET with pagination params
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 10)), 50)
        qs = ThreadView.objects.filter(user_id=target_user).select_related('thread_id').order_by('-viewed_at')
        total = qs.count()
        start = (page - 1) * limit
        end = start + limit
        items = qs[start:end]
        # Build minimal payload
        results = [
            {
                'thread_id': tv.thread_id.id,
                'title': tv.thread_id.title,
                'author_display_name': tv.thread_id.get_author_display_name(),
                'viewed_at': tv.viewed_at.isoformat(),
            }
            for tv in items
        ]
        return Response({'results': results, 'page': page, 'limit': limit, 'total': total})

    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """Return threads liked by this user (status=True), paginated."""
        try:
            target_user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 10)), 50)
        qs = ThreadLike.objects.filter(user_id=target_user, status=True).select_related('thread_id').order_by('-create_time')
        total = qs.count()
        start = (page - 1) * limit
        end = start + limit
        slice_qs = qs[start:end]
        results = [
            {
                'thread_id': tl.thread_id.id,
                'title': tl.thread_id.title,
                'author_display_name': tl.thread_id.get_author_display_name(),
                'liked_at': tl.create_time.isoformat(),
            }
            for tl in slice_qs
        ]
        return Response({'results': results, 'page': page, 'limit': limit, 'total': total})

    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def ban(self, request, pk=None):
        """Ban a user (set is_banned=True) and soft delete their content."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Don't allow banning admin users
        if user.is_admin or user.is_staff or user.is_superuser:
            return Response({'error': 'Cannot ban admin users'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_banned = True
        user.save()
        
        # Soft delete all threads created by this user
        Thread.objects.filter(user_id=user).update(is_deleted=True)
        
        # Soft delete all replies created by this user
        Reply.objects.filter(user_id=user).update(is_deleted=True)
        
        # Disable all likes given by this user
        from forum.models import ThreadLike, ReplyLike
        ThreadLike.objects.filter(user_id=user).update(status=False)
        ReplyLike.objects.filter(user_id=user).update(status=False)
        
        return Response({
            'success': True, 
            'user_id': user.id, 
            'is_banned': user.is_banned,
            'message': f'User banned and {Thread.objects.filter(user_id=user).count()} threads and {Reply.objects.filter(user_id=user).count()} replies soft deleted, likes disabled'
        })

    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def unban(self, request, pk=None):
        """Unban a user (set is_banned=False) and restore their content."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user.is_banned = False
        user.save()
        
        # Restore all threads created by this user
        Thread.objects.filter(user_id=user).update(is_deleted=False)
        
        # Restore all replies created by this user
        Reply.objects.filter(user_id=user).update(is_deleted=False)
        
        # Restore all likes given by this user
        from forum.models import ThreadLike, ReplyLike
        ThreadLike.objects.filter(user_id=user).update(status=True)
        ReplyLike.objects.filter(user_id=user).update(status=True)
        
        return Response({
            'success': True, 
            'user_id': user.id, 
            'is_banned': user.is_banned,
            'message': f'User unbanned and {Thread.objects.filter(user_id=user).count()} threads and {Reply.objects.filter(user_id=user).count()} replies restored, likes enabled'
        })


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tag CRUD operations.
    
    Provides endpoints for:
    - GET /api/tags/ - List all tags (active only for non-admin users)
    - POST /api/tags/ - Create new tag (admin only)
    - GET /api/tags/{name}/ - Retrieve specific tag
    - PUT/PATCH /api/tags/{name}/ - Update tag (admin only)
    - DELETE /api/tags/{name}/ - Disable tag (admin only)
    
    Query parameters:
    - search: Search in tag name (e.g., ?search=python)
    """
    queryset = Tag.objects.all()
    lookup_field = 'name'
    filter_backends = [SearchFilter]
    search_fields = ['name']
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return TagCreateSerializer
        return TagSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsCustomAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Return active tags for non-admin users, all tags for admin users.
        """
        user = getattr(self.request, 'user', None)
        is_admin_user = bool(user) and (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False))
        
        if is_admin_user:
            return Tag.objects.all().order_by('name')
        else:
            return Tag.objects.filter(is_active=True).order_by('name')
    
    def perform_destroy(self, instance):
        """
        Soft delete by setting is_active=False instead of actually deleting.
        """
        instance.is_active = False
        instance.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def enable(self, request, name=None):
        """Enable a tag (set is_active=True)."""
        try:
            tag = Tag.objects.get(name=name)
        except Tag.DoesNotExist:
            return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)
        
        tag.is_active = True
        tag.save()
        return Response({
            'success': True,
            'tag_name': tag.name,
            'is_active': tag.is_active,
            'message': 'Tag enabled successfully'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsCustomAdminUser])
    def disable(self, request, name=None):
        """Disable a tag (set is_active=False)."""
        try:
            tag = Tag.objects.get(name=name)
        except Tag.DoesNotExist:
            return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)
        
        tag.is_active = False
        tag.save()
        return Response({
            'success': True,
            'tag_name': tag.name,
            'is_active': tag.is_active,
            'message': 'Tag disabled successfully'
        })


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Category read operations.
    
    Provides read-only endpoints for:
    - GET /api/categories/ - List categories
    - GET /api/categories/{id}/ - Retrieve specific category
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class LoginAPIView(APIView):
    """
    API endpoint for user authentication.
    
    POST /api/auth/login/
    Body: {"email": "user@example.com", "password": "password"}
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle login request."""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic rate limit and lockout using cache
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        fail_key = f"auth:fail:{ip}:{email}"
        lock_key = f"auth:lock:{ip}:{email}"
        if cache.get(lock_key):
            return Response({'error': 'Too many attempts. Try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = authenticate(request, username=email, password=password)
        if not user:
            # Check if user exists but is banned
            try:
                existing_user = User.objects.get(email=email)
                if getattr(existing_user, 'is_banned', False):
                    return Response({
                        'error': 'Your account has been banned. Please contact the administrator.',
                        'banned': True
                    }, status=status.HTTP_403_FORBIDDEN)
            except User.DoesNotExist:
                try:
                    existing_user = User.objects.get(username=email)
                    if getattr(existing_user, 'is_banned', False):
                        return Response({
                            'error': 'Your account has been banned. Please contact the administrator.',
                            'banned': True
                        }, status=status.HTTP_403_FORBIDDEN)
                except User.DoesNotExist:
                    pass
            
            fails = cache.get(fail_key, 0) + 1
            cache.set(fail_key, fails, timeout=600)  # 10 minutes window
            if fails >= 5:
                cache.set(lock_key, True, timeout=600)
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # If password passes, send OTP to email and store in cache
        import random
        otp = f"{random.randint(100000, 999999)}"
        otp_key = f"auth:otp:{user.id}"
        cache.set(otp_key, otp, timeout=300)  # 5 minutes
        # Use backend email service (Mailjet with fallback). Send to plain email from request for reliability
        logger = logging.getLogger(__name__)
        recipient_email = email
        try:
            result = email_service.send_otp_with_retry(to_email=recipient_email, otp_code=otp, user_id=user.id)
        except Exception as e:
            logger.error(f"OTP send raised: {e}")
            result = {'success': False, 'error': str(e)}

        if not result.get('success'):
            logger.error(f"Failed to send OTP email to user {user.id}: {result.get('error')}")
            return Response({
                'mfa_required': True,
                'user_id': user.id,
                'message': 'OTP sent to your email (delivery may be delayed)',
                'email_status': 'pending'
            })

        return Response({
            'mfa_required': True,
            'user_id': user.id,
            'message': 'OTP sent to your email',
            'email_status': 'sent',
            'delivery_method': result.get('method', 'unknown')
        })


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle logout request."""
        logout(request)
        return Response({'success': True, 'message': 'Logout successful'})


class RegisterAPIView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    Body: {"email": "user@example.com", "password": "password", "confirm_password": "password", "username": "用户昵称"}
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle registration request."""
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        username = request.data.get('username')
        is_admin = request.data.get('is_admin', False)
        
        if not email or not password or not confirm_password or not username:
            return Response(
                {'error': 'All fields are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if password != confirm_password:
            return Response(
                {'error': 'Passwords do not match'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate username
        username = str(username).strip()
        if len(username) == 0:
            return Response({'error': 'Username cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        if len(username) > 50:
            return Response({'error': 'Username too long (max 50)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Enforce password complexity using Django validators
        try:
            validate_password(password)
        except DjangoValidationError as e:
            return Response({'error': ' '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            # Set admin status if requested
            if is_admin:
                user.is_admin = True
                user.save()
        except Exception as e:
            return Response({'error': 'Failed to create user'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'message': 'Registration successful'})


class VerifyOTPAPIView(APIView):
    """
    Verify OTP to complete MFA login.
    POST /api/auth/verify-otp/
    Body: {"user_id": 1, "otp": "123456"}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')
        if not user_id or not otp:
            return Response({'error': 'user_id and otp are required'}, status=status.HTTP_400_BAD_REQUEST)

        otp_key = f"auth:otp:{user_id}"
        cached = cache.get(otp_key)
        if not cached or cached != otp:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is banned
        if getattr(user, 'is_banned', False):
            cache.delete(otp_key)  # Clear OTP even if user is banned
            return Response({'error': 'Account is banned. Please contact administrator.'}, status=status.HTTP_403_FORBIDDEN)

        # OTP valid -> log the user in and clear OTP
        cache.delete(otp_key)
        login(request, user)
        return Response({
            'success': True,
            'message': 'Login successful',
            'user_id': user.id,
            'username': user.username,
            'is_staff': getattr(user, 'is_staff', False),
            'is_superuser': getattr(user, 'is_superuser', False),
            'is_admin': getattr(user, 'is_admin', False),
        })


@method_decorator(csrf_exempt, name='dispatch')
class ResendOTPAPIView(APIView):
    """
    Resend OTP code to user's email.
    POST /api/auth/resend-otp/
    Body: {"user_id": 1, "email": "user@example.com"}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is banned
        if getattr(user, 'is_banned', False):
            return Response({'error': 'Account is banned. Please contact administrator.'}, status=status.HTTP_403_FORBIDDEN)

        # Use provided email or get from user (decrypt if needed)
        recipient_email = email
        if not recipient_email:
            # Try to get email from user model
            recipient_email = getattr(user, 'email', '')
            # If email is encrypted, try to decrypt it
            if recipient_email and '@' not in recipient_email:
                try:
                    recipient_email = email_service.decrypt_user_email(recipient_email)
                except Exception:
                    pass
        
        if not recipient_email or '@' not in recipient_email:
            return Response({'error': 'Email address is required. Please provide email in request.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate new OTP
        import random
        otp = f"{random.randint(100000, 999999)}"
        otp_key = f"auth:otp:{user_id}"
        cache.set(otp_key, otp, timeout=300)  # 5 minutes

        # Send OTP via email service (with rate limiting built-in)
        logger = logging.getLogger(__name__)
        try:
            result = email_service.send_otp_with_retry(to_email=recipient_email, otp_code=otp, user_id=user.id)
        except Exception as e:
            logger.error(f"OTP resend raised: {e}")
            result = {'success': False, 'error': str(e)}

        if not result.get('success'):
            error_msg = result.get('error', 'Failed to send OTP email')
            logger.error(f"Failed to resend OTP email to user {user.id}: {error_msg}")
            
            # Check if it's a rate limit error
            if 'rate limit' in error_msg.lower():
                # Extract rate limit seconds from settings for error message
                rate_limit_seconds = getattr(settings, 'EMAIL_RATE_LIMIT_SECONDS', 10)
                return Response({
                    'success': False,
                    'error': f'OTP requests are limited to once every {rate_limit_seconds} seconds. Please wait before requesting another OTP.',
                    'rate_limited': True
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            return Response({
                'success': False,
                'error': error_msg,
                'message': 'Failed to resend OTP. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'message': 'OTP code has been resent to your email',
            'email_status': 'sent',
            'delivery_method': result.get('method', 'unknown')
        })


class ThreadRepliesAPIView(APIView):
    """
    API endpoint to get replies for a specific thread.
    
    GET /api/threads/{thread_id}/replies/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, thread_id):
        """Get all replies for a thread."""
        try:
            thread = Thread.objects.get(pk=thread_id)
        except Thread.DoesNotExist:
            return Response({'error': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        
        replies = Reply.objects.filter(thread_id=thread, is_deleted=False).order_by('create_time')
        serializer = ReplySerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class ThreadLikeAPIView(APIView):
    """
    API endpoint to like/unlike a thread.
    
    POST /api/threads/{thread_id}/like/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, thread_id):
        """Toggle like status for a thread."""
        try:
            thread = Thread.objects.get(pk=thread_id)
        except Thread.DoesNotExist:
            return Response({'error': 'Thread not found'}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = ThreadLike.objects.get_or_create(
            user_id=request.user, thread_id=thread
        )
        if not created:
            like.status = not like.status
            like.save()
        else:
            like.status = True
            like.save()
        
        return Response({
            'liked': like.status,
            'like_count': ThreadLike.objects.filter(thread_id=thread, status=True).count()
        })


class ReplyLikeAPIView(APIView):
    """
    API endpoint to like/unlike a reply.
    
    POST /api/replies/{reply_id}/like/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, reply_id):
        """Toggle like status for a reply."""
        try:
            reply = Reply.objects.get(pk=reply_id)
        except Reply.DoesNotExist:
            return Response({'error': 'Reply not found'}, status=status.HTTP_404_NOT_FOUND)
        
        like, created = ReplyLike.objects.get_or_create(
            user_id=request.user, reply_id=reply
        )
        if not created:
            like.status = not like.status
            like.save()
        else:
            like.status = True
            like.save()
        
        return Response({
            'liked': like.status,
            'like_count': ReplyLike.objects.filter(reply_id=reply, status=True).count()
        })


class SearchAPIView(APIView):
    """
    API endpoint for searching threads and replies.
    
    GET /api/search/?q=search_term&type=threads&sort=recent&page=1&limit=20
    Query parameters:
    - q: Search query (required)
    - type: Search type - 'threads', 'replies', or 'all' (default: 'all')
    - sort: Sort order - 'recent', 'popular', 'relevance' (default: 'recent')
    - page: Page number for pagination (default: 1)
    - limit: Number of results per page (default: 20, max: 100)
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Search threads and replies by title and body content."""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(query) > 100:
            return Response({'error': 'Search query too long (max 100 characters)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get search parameters
        search_type = request.query_params.get('type', 'all')
        sort_order = request.query_params.get('sort', 'recent')
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 20)), 100)
        
        # Validate parameters
        if search_type not in ['threads', 'replies', 'all']:
            return Response({'error': 'Invalid search type. Use: threads, replies, or all'}, status=status.HTTP_400_BAD_REQUEST)
        
        if sort_order not in ['recent', 'popular', 'relevance']:
            return Response({'error': 'Invalid sort order. Use: recent, popular, or relevance'}, status=status.HTTP_400_BAD_REQUEST)
        
        results = {
            'query': query,
            'type': search_type,
            'sort': sort_order,
            'page': page,
            'limit': limit,
            'threads': [],
            'replies': [],
            'total_threads': 0,
            'total_replies': 0,
            'total_results': 0
        }
        
        # Search threads
        if search_type in ['threads', 'all']:
            threads = self._search_threads(query, sort_order, page, limit)
            results['threads'] = threads['results']
            results['total_threads'] = threads['total']
        
        # Search replies
        if search_type in ['replies', 'all']:
            replies = self._search_replies(query, sort_order, page, limit)
            results['replies'] = replies['results']
            results['total_replies'] = replies['total']
        
        results['total_results'] = results['total_threads'] + results['total_replies']
        
        return Response(results)
    
    def _search_threads(self, query, sort_order, page, limit):
        """Search threads by title and body content."""
        # Base query for non-deleted threads
        threads = Thread.objects.filter(is_deleted=False)
        
        # Search in title and body
        search_query = Q(title__icontains=query) | Q(body__icontains=query)
        threads = threads.filter(search_query)
        
        # Apply sorting
        if sort_order == 'recent':
            threads = threads.order_by('-create_time')
        elif sort_order == 'popular':
            # Sort by like count (we'll add this later)
            threads = threads.annotate(
                like_count=Count('threadlike', filter=Q(threadlike__status=True))
            ).order_by('-like_count', '-create_time')
        elif sort_order == 'relevance':
            # Simple relevance: title matches first, then body matches
            threads = threads.extra(
                select={
                    'relevance': """
                        CASE 
                            WHEN title LIKE %s THEN 3
                            WHEN body LIKE %s THEN 1
                            ELSE 0
                        END
                    """
                },
                select_params=[f'%{query}%', f'%{query}%']
            ).order_by('-relevance', '-create_time')
        
        # Get total count
        total = threads.count()
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        threads = threads[start:end]
        
        # Serialize results
        serializer = ThreadListSerializer(threads, many=True)
        
        return {
            'results': serializer.data,
            'total': total
        }
    
    def _search_replies(self, query, sort_order, page, limit):
        """Search replies by body content."""
        # Base query for non-deleted replies
        replies = Reply.objects.filter(is_deleted=False)
        
        # Search in body
        replies = replies.filter(body__icontains=query)
        
        # Apply sorting
        if sort_order == 'recent':
            replies = replies.order_by('-create_time')
        elif sort_order == 'popular':
            # Sort by like count (using existing like_count field)
            replies = replies.order_by('-like_count', '-create_time')
        elif sort_order == 'relevance':
            # Simple relevance: body matches
            replies = replies.extra(
                select={
                    'relevance': """
                        CASE 
                            WHEN body LIKE %s THEN 2
                            ELSE 0
                        END
                    """
                },
                select_params=[f'%{query}%']
            ).order_by('-relevance', '-create_time')
        
        # Get total count
        total = replies.count()
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        replies = replies[start:end]
        
        # Serialize results
        serializer = ReplySerializer(replies, many=True)
        
        return {
            'results': serializer.data,
            'total': total
        }


class ToggleAnonymousModeAPIView(APIView):
    """
    API endpoint to toggle user's anonymous mode.
    
    POST /api/auth/toggle-anonymous/
    Body: {"is_anonymous": true/false}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Toggle user's anonymous mode."""
        is_anonymous = request.data.get('is_anonymous', False)
        
        user = request.user
        # Prevent admin users from using anonymous mode
        is_admin_user = getattr(user, 'is_admin', False) or getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
        if is_admin_user:
            # Force admin users to non-anonymous mode
            user.is_anonymous = False
            user.save()
            return Response({
                'success': True,
                'is_anonymous': False,
                'message': 'Admin users cannot use anonymous mode'
            })
        
        user.is_anonymous = is_anonymous
        user.save()
        
        return Response({
            'success': True,
            'is_anonymous': user.is_anonymous,
            'message': f'Anonymous mode {"enabled" if is_anonymous else "disabled"}'
        })


@method_decorator(ensure_csrf_cookie, name='get')
@method_decorator(ensure_csrf_cookie, name='get')
class WhoAmIAPIView(APIView):
    """
    API endpoint to get current user's authentication status.
    
    GET /api/auth/whoami/
    Returns current user info or indicates not logged in.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current user's authentication status."""
        if request.user.is_authenticated:
            return Response({
                'logged_in': True,
                'user_id': request.user.id,
                'username': request.user.username,
                'is_anonymous': getattr(request.user, 'is_anonymous', False),
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'is_admin': getattr(request.user, 'is_admin', False),
            })
        else:
            return Response({
                'logged_in': False,
            })
