"""
Serializers for RESTful API endpoints.

This module defines serializers for converting Django model instances
to JSON format and vice versa for API communication.
"""

from rest_framework import serializers
from forum.models import User, Thread, Reply, Tag, Category, ThreadLike, ReplyLike, ThreadTags
import re


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    thread_count = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='create_time', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'is_admin', 'is_staff', 'is_superuser', 
            'is_anonymous', 'is_active', 'is_banned', 'create_time', 'update_time', 
            'thread_count', 'reply_count', 'date_joined'
        ]
        read_only_fields = ['id', 'create_time', 'update_time']
    
    def get_thread_count(self, obj):
        """Get the number of threads created by this user."""
        return Thread.objects.filter(user_id=obj, is_deleted=False).count()
    
    def get_reply_count(self, obj):
        """Get the number of replies created by this user."""
        return Reply.objects.filter(user_id=obj, is_deleted=False).count()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    class Meta:
        model = Category
        fields = ['id', 'name']


class TagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tags."""
    
    class Meta:
        model = Tag
        fields = ['name']
    
    def validate_name(self, value):
        """Validate tag name format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Tag name cannot be empty")
        
        # Convert to lowercase and remove extra spaces
        value = value.strip().lower()
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError("Tag name can only contain lowercase letters, numbers, hyphens, and underscores")
        
        # Check length
        if len(value) < 2:
            raise serializers.ValidationError("Tag name must be at least 2 characters long")
        if len(value) > 50:
            raise serializers.ValidationError("Tag name cannot exceed 50 characters")
        
        # Check if tag already exists
        if Tag.objects.filter(name=value).exists():
            raise serializers.ValidationError("A tag with this name already exists")
        
        return value


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    thread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['name', 'is_active', 'thread_count']
        read_only_fields = ['name']  # Name cannot be changed after creation
    
    def get_thread_count(self, obj):
        """Get the number of threads using this tag."""
        return ThreadTags.objects.filter(tag_id=obj, thread_id__is_deleted=False).count()
    
    def validate_name(self, value):
        """Validate tag name format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Tag name cannot be empty")
        
        # Convert to lowercase and remove extra spaces
        value = value.strip().lower()
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-z0-9_-]+$', value):
            raise serializers.ValidationError("Tag name can only contain lowercase letters, numbers, hyphens, and underscores")
        
        # Check length
        if len(value) < 2:
            raise serializers.ValidationError("Tag name must be at least 2 characters long")
        if len(value) > 50:
            raise serializers.ValidationError("Tag name cannot exceed 50 characters")
        
        return value


class ThreadTagsSerializer(serializers.ModelSerializer):
    """Serializer for ThreadTags relationship."""
    tag = TagSerializer(read_only=True)
    
    class Meta:
        model = ThreadTags
        fields = ['tag']


class ThreadSerializer(serializers.ModelSerializer):
    """Serializer for Thread model with related data."""
    author = UserSerializer(source='user_id', read_only=True)
    author_display_name = serializers.SerializerMethodField()
    username = serializers.CharField(source='user_id.username', read_only=True)
    category = CategorySerializer(source='category_id', read_only=True)
    category_name = serializers.CharField(source='category_id.name', read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    tags = ThreadTagsSerializer(source='threadtags', many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        help_text="List of tag names to associate with this thread"
    )
    is_anonymous = serializers.BooleanField(write_only=True, required=False, default=False)
    like_count = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    tags_flat = serializers.SerializerMethodField()
    
    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'body', 'author', 'author_display_name', 'username', 
            'category', 'category_name', 'category_id', 'user_id',
            'tags', 'tag_names', 'is_anonymous', 'like_count', 'reply_count', 'tags_flat',
            'create_time', 'edit_time', 'is_deleted'
        ]
        read_only_fields = ['id', 'user_id', 'create_time', 'edit_time', 'is_deleted']
    
    def get_like_count(self, obj):
        """Get the number of likes for this thread."""
        return ThreadLike.objects.filter(thread_id=obj, status=True).count()
    
    def get_reply_count(self, obj):
        """Get the number of replies for this thread."""
        return Reply.objects.filter(thread_id=obj, is_deleted=False).count()
    
    def get_author_display_name(self, obj):
        """Get display name; admins always see real username."""
        request = self.context.get('request', None) if self.context else None
        if request:
            user = getattr(request, 'user', None)
            if user:
                is_admin_user = bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False))
                if is_admin_user:
                    return obj.user_id.username
        return obj.get_author_display_name()
    
    def get_tags_flat(self, obj):
        return list(ThreadTags.objects.filter(thread_id=obj, tag_id__is_active=True).values_list('tag_id__name', flat=True))
    
    def validate_tag_names(self, value):
        """Validate tag names and check if they are available."""
        if not value:
            return value
        
        # Remove duplicates and empty strings
        unique_tags = list(set([tag.strip() for tag in value if tag.strip()]))
        
        # Validate tag names format
        for tag_name in unique_tags:
            if len(tag_name) > 100:
                raise serializers.ValidationError(f"Tag name '{tag_name}' is too long (max 100 characters)")
            if not tag_name.replace('-', '').replace('_', '').isalnum():
                raise serializers.ValidationError(f"Tag name '{tag_name}' contains invalid characters. Only letters, numbers, hyphens, and underscores are allowed")
        
        # Check if all tags are available (exist and active)
        unavailable_tags = []
        for tag_name in unique_tags:
            try:
                tag = Tag.objects.get(name=tag_name)
                if not tag.is_active:
                    unavailable_tags.append(tag_name)
            except Tag.DoesNotExist:
                # New tags are allowed (will be created as active)
                pass
        
        if unavailable_tags:
            raise serializers.ValidationError(
                f"The following tags are not available: {', '.join(unavailable_tags)}. Please remove them or contact admin to enable them."
            )
        
        return unique_tags
    
    def validate_category_id(self, value):
        """Validate that the category exists."""
        try:
            Category.objects.get(pk=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category does not exist.")
        return value
    
    def create(self, validated_data):
        """Create a new thread with tags and handle anonymous mode."""
        tag_names = validated_data.pop('tag_names', [])
        is_anonymous = validated_data.pop('is_anonymous', False)
        
        # Convert primitive category_id to Category instance
        category_pk = validated_data.pop('category_id')
        category = Category.objects.get(pk=category_pk)
        
        # Set thread's anonymous status
        validated_data['is_anonymous'] = is_anonymous
        
        thread = Thread.objects.create(category_id=category, **validated_data)
        
        # Add tags to the thread (create new tags if they don't exist)
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'is_active': True}
            )
            ThreadTags.objects.get_or_create(thread_id=thread, tag_id=tag)
        
        return thread
    
    def update(self, instance, validated_data):
        """Update thread and handle tag changes."""
        tag_names = validated_data.pop('tag_names', None)
        # Never allow changing anonymity on edit
        validated_data.pop('is_anonymous', None)
        
        # Handle category_id if provided
        if 'category_id' in validated_data:
            category_pk = validated_data.pop('category_id')
            if category_pk is not None:
                try:
                    category = Category.objects.get(pk=category_pk)
                    validated_data['category_id'] = category
                except Category.DoesNotExist:
                    raise serializers.ValidationError("Category does not exist.")
        
        # Update thread fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_names is not None:
            # Remove existing tags
            ThreadTags.objects.filter(thread_id=instance).delete()
            # Add new tags (create new tags if they don't exist)
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'is_active': True}
                )
                ThreadTags.objects.get_or_create(thread_id=instance, tag_id=tag)
        
        return instance


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for Reply model."""
    author = UserSerializer(source='user_id', read_only=True)
    author_display_name = serializers.SerializerMethodField()
    thread_id = serializers.IntegerField(write_only=True, required=False)
    thread_title = serializers.CharField(source='thread_id.title', read_only=True)
    is_anonymous = serializers.BooleanField(required=False, default=False)
    like_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Reply
        fields = [
            'id', 'body', 'author', 'author_display_name', 'thread_id', 'thread_title',
            'is_anonymous', 'like_count', 'create_time', 'edit_time', 'is_deleted'
        ]
        read_only_fields = ['id', 'create_time', 'edit_time', 'is_deleted']
    
    def get_like_count(self, obj):
        """Get the number of likes for this reply."""
        return ReplyLike.objects.filter(reply_id=obj, status=True).count()
    
    def get_author_display_name(self, obj):
        """Get display name; admins always see real username."""
        request = self.context.get('request', None) if self.context else None
        if request:
            user = getattr(request, 'user', None)
            if user:
                is_admin_user = bool(getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False) or getattr(user, 'is_admin', False))
                if is_admin_user:
                    return obj.user_id.username
        return obj.get_author_display_name()

    def create(self, validated_data):
        """Create reply mapping primitive thread_id to Thread instance and handle anonymous mode."""
        thread_pk = validated_data.pop('thread_id', None)
        if thread_pk is None:
            raise serializers.ValidationError({'thread_id': 'This field is required.'})
        
        # Get is_anonymous from validated_data
        is_anonymous = validated_data.get('is_anonymous', False)
        
        # DEBUG: Print debug info
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[REPLY CREATE] thread_pk={thread_pk}, is_anonymous={is_anonymous}, validated_data={validated_data}")
        
        thread = Thread.objects.get(pk=thread_pk)
        
        # Preserve user_id from validated_data if present (from perform_create)
        user_id = validated_data.pop('user_id', None)
        
        # Create reply with is_anonymous explicitly set
        validated_data['is_anonymous'] = is_anonymous
        logger.info(f"[REPLY CREATE] Creating with is_anonymous={is_anonymous}, user_id={user_id}")
        
        # Create reply with all validated data
        if user_id:
            reply = Reply.objects.create(thread_id=thread, user_id=user_id, **validated_data)
        else:
            reply = Reply.objects.create(thread_id=thread, **validated_data)
        
        logger.info(f"[REPLY CREATE] Created reply id={reply.id}, is_anonymous={reply.is_anonymous}")
        return reply
    
    def update(self, instance, validated_data):
        """Update reply body only; do not change thread_id or anonymity on edit."""
        # Never allow changing anonymity or thread mapping on edit
        validated_data.pop('is_anonymous', None)
        validated_data.pop('thread_id', None)
        
        instance.body = validated_data.get('body', instance.body)
        instance.save()
        return instance


class ThreadLikeSerializer(serializers.ModelSerializer):
    """Serializer for ThreadLike model."""
    thread_id = serializers.IntegerField(write_only=True)
    thread_title = serializers.CharField(source='thread_id.title', read_only=True)
    
    class Meta:
        model = ThreadLike
        fields = ['id', 'thread_id', 'thread_title', 'status', 'create_time']
        read_only_fields = ['id', 'create_time']


class ReplyLikeSerializer(serializers.ModelSerializer):
    """Serializer for ReplyLike model."""
    reply_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ReplyLike
        fields = ['id', 'reply_id', 'status', 'create_time']
        read_only_fields = ['id', 'create_time']


class ThreadListSerializer(serializers.ModelSerializer):
    """Simplified serializer for thread list view."""
    author = UserSerializer(source='user_id', read_only=True)
    username = serializers.CharField(source='user_id.username', read_only=True)
    author_display_name = serializers.SerializerMethodField()
    category = CategorySerializer(source='category_id', read_only=True)
    category_name = serializers.CharField(source='category_id.name', read_only=True)
    tags = ThreadTagsSerializer(source='threadtags', many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    tags_flat = serializers.SerializerMethodField()
    
    class Meta:
        model = Thread
        fields = [
            'id', 'title', 'author', 'username', 'author_display_name', 'category', 'category_name', 'tags', 'tags_flat',
            'like_count', 'reply_count', 'create_time', 'is_deleted', 'is_anonymous', 'user_id'
        ]
    
    def get_author_display_name(self, obj):
        """Return anonymous display name if thread is anonymous, otherwise username."""
        return obj.get_author_display_name()
    
    def get_like_count(self, obj):
        return ThreadLike.objects.filter(thread_id=obj, status=True).count()
    
    def get_reply_count(self, obj):
        return Reply.objects.filter(thread_id=obj, is_deleted=False).count()
    
    def get_tags_flat(self, obj):
        return list(ThreadTags.objects.filter(thread_id=obj, tag_id__is_active=True).values_list('tag_id__name', flat=True))
