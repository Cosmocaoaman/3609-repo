"""
Comprehensive test suite for API serializers.

This module contains tests for all serializers including validation,
serialization, deserialization, and edge cases. Tests cover both
success and error scenarios for all serializer classes.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import serializers
from unittest.mock import Mock

from forum.models import (
    User, Category, Tag, Thread, Reply, ThreadTags, 
    ThreadLike, ReplyLike
)
from api.serializers import (
    UserSerializer, ThreadSerializer, ReplySerializer, TagSerializer,
    TagCreateSerializer, CategorySerializer, ThreadLikeSerializer,
    ReplyLikeSerializer, ThreadListSerializer, ThreadTagsSerializer
)


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        self.reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
    
    def test_user_serialization(self):
        """Test user serialization."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['id'], self.user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertFalse(data['is_admin'])
        self.assertFalse(data['is_anonymous'])
        self.assertFalse(data['is_banned'])
        self.assertIsNotNone(data['create_time'])
        self.assertIsNotNone(data['update_time'])
    
    def test_user_thread_count(self):
        """Test thread count calculation."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['thread_count'], 1)
    
    def test_user_reply_count(self):
        """Test reply count calculation."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['reply_count'], 1)
    
    def test_user_date_joined_field(self):
        """Test date_joined field mapping."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        
        self.assertEqual(data['date_joined'], self.user.create_time)


class CategorySerializerTest(TestCase):
    """Test cases for CategorySerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.category = Category.objects.create(name='Academic')
    
    def test_category_serialization(self):
        """Test category serialization."""
        serializer = CategorySerializer(self.category)
        data = serializer.data
        
        self.assertEqual(data['id'], self.category.id)
        self.assertEqual(data['name'], 'Academic')


class TagCreateSerializerTest(TestCase):
    """Test cases for TagCreateSerializer."""
    
    def test_tag_creation_valid_name(self):
        """Test creating tag with valid name."""
        data = {'name': 'python'}
        serializer = TagCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        
        self.assertEqual(tag.name, 'python')
        self.assertTrue(tag.is_active)
    
    def test_tag_creation_empty_name(self):
        """Test creating tag with empty name."""
        data = {'name': ''}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_whitespace_name(self):
        """Test creating tag with whitespace-only name."""
        data = {'name': '   '}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_invalid_characters(self):
        """Test creating tag with invalid characters."""
        data = {'name': 'python@#$'}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_too_short(self):
        """Test creating tag with name too short."""
        data = {'name': 'a'}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_too_long(self):
        """Test creating tag with name too long."""
        data = {'name': 'x' * 51}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_duplicate_name(self):
        """Test creating tag with duplicate name."""
        Tag.objects.create(name='python')
        
        data = {'name': 'python'}
        serializer = TagCreateSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_tag_creation_normalizes_name(self):
        """Test that tag name is normalized to lowercase."""
        data = {'name': 'PYTHON'}
        serializer = TagCreateSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        
        self.assertEqual(tag.name, 'python')


class TagSerializerTest(TestCase):
    """Test cases for TagSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.tag = Tag.objects.create(name='python')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        ThreadTags.objects.create(thread_id=self.thread, tag_id=self.tag)
    
    def test_tag_serialization(self):
        """Test tag serialization."""
        serializer = TagSerializer(self.tag)
        data = serializer.data
        
        self.assertEqual(data['name'], 'python')
        self.assertTrue(data['is_active'])
        self.assertEqual(data['thread_count'], 1)
    
    def test_tag_thread_count(self):
        """Test thread count calculation."""
        serializer = TagSerializer(self.tag)
        data = serializer.data
        
        self.assertEqual(data['thread_count'], 1)
    
    def test_tag_thread_count_excludes_deleted(self):
        """Test that thread count excludes deleted threads."""
        self.thread.is_deleted = True
        self.thread.save()
        
        serializer = TagSerializer(self.tag)
        data = serializer.data
        
        self.assertEqual(data['thread_count'], 0)


class ThreadTagsSerializerTest(TestCase):
    """Test cases for ThreadTagsSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        self.tag = Tag.objects.create(name='python')
        self.thread_tag = ThreadTags.objects.create(
            thread_id=self.thread,
            tag_id=self.tag
        )
    
    def test_thread_tags_serialization(self):
        """Test thread-tag relationship serialization."""
        serializer = ThreadTagsSerializer(self.thread_tag)
        data = serializer.data
        
        self.assertIn('tag', data)
        self.assertEqual(data['tag']['name'], 'python')


class ThreadSerializerTest(TestCase):
    """Test cases for ThreadSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.tag = Tag.objects.create(name='python')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        ThreadTags.objects.create(thread_id=self.thread, tag_id=self.tag)
    
    def test_thread_serialization(self):
        """Test thread serialization."""
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['id'], self.thread.id)
        self.assertEqual(data['title'], 'Test Thread')
        self.assertEqual(data['body'], 'Test body')
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['category_id'], self.category.id)
        self.assertFalse(data['is_deleted'])
        self.assertIsNotNone(data['create_time'])
        self.assertIsNotNone(data['edit_time'])
    
    def test_thread_author_display_name_normal(self):
        """Test author display name for normal thread."""
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_thread_author_display_name_anonymous(self):
        """Test author display name for anonymous thread."""
        self.thread.is_anonymous = True
        self.thread.save()
        
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(data['author_display_name'], expected_name)
    
    def test_thread_author_display_name_admin_view(self):
        """Test author display name for admin view."""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_admin=True
        )
        
        self.thread.is_anonymous = True
        self.thread.save()
        
        # Mock request context with admin user
        mock_request = Mock()
        mock_request.user = admin_user
        
        serializer = ThreadSerializer(self.thread, context={'request': mock_request})
        data = serializer.data
        
        # Admin should see real username even for anonymous threads
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_thread_like_count(self):
        """Test like count calculation."""
        # Create some likes
        ThreadLike.objects.create(
            user_id=self.user,
            thread_id=self.thread,
            status=True
        )
        
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['like_count'], 1)
    
    def test_thread_reply_count(self):
        """Test reply count calculation."""
        # Create a reply
        Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
        
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['reply_count'], 1)
    
    def test_thread_tags_flat(self):
        """Test tags_flat field."""
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        self.assertIn('python', data['tags_flat'])
    
    def test_thread_creation_with_tags(self):
        """Test thread creation with tags."""
        data = {
            'title': 'New Thread',
            'body': 'New body',
            'category_id': self.category.id,
            'tag_names': ['python', 'django'],
            'is_anonymous': False
        }
        
        serializer = ThreadSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        thread = serializer.save(user_id=self.user)
        
        self.assertEqual(thread.title, 'New Thread')
        self.assertEqual(thread.body, 'New body')
        self.assertFalse(thread.is_anonymous)
        
        # Check tags were created and associated
        self.assertEqual(ThreadTags.objects.filter(thread_id=thread).count(), 2)
    
    def test_thread_creation_invalid_category(self):
        """Test thread creation with invalid category."""
        data = {
            'title': 'New Thread',
            'body': 'New body',
            'category_id': 99999,  # Non-existent category
            'tag_names': ['python']
        }
        
        serializer = ThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('category_id', serializer.errors)
    
    def test_thread_creation_invalid_tags(self):
        """Test thread creation with invalid tags."""
        # Create an inactive tag
        inactive_tag = Tag.objects.create(name='inactive', is_active=False)
        
        data = {
            'title': 'New Thread',
            'body': 'New body',
            'category_id': self.category.id,
            'tag_names': ['python', 'inactive']
        }
        
        serializer = ThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tag_names', serializer.errors)
    
    def test_thread_update_tags(self):
        """Test updating thread tags."""
        data = {
            'title': 'Updated Thread',
            'body': 'Updated body',
            'tag_names': ['django', 'web']
        }
        
        serializer = ThreadSerializer(self.thread, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_thread = serializer.save()
        
        # Check old tags were removed and new ones added
        self.assertEqual(ThreadTags.objects.filter(thread_id=updated_thread).count(), 2)
        tag_names = list(ThreadTags.objects.filter(thread_id=updated_thread).values_list('tag_id__name', flat=True))
        self.assertIn('django', tag_names)
        self.assertIn('web', tag_names)
    
    def test_thread_update_preserves_anonymity(self):
        """Test that thread update doesn't change anonymity."""
        self.thread.is_anonymous = True
        self.thread.save()
        
        data = {
            'title': 'Updated Thread',
            'body': 'Updated body',
            'is_anonymous': False  # This should be ignored
        }
        
        serializer = ThreadSerializer(self.thread, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_thread = serializer.save()
        
        # Anonymity should be preserved
        self.assertTrue(updated_thread.is_anonymous)


class ThreadListSerializerTest(TestCase):
    """Test cases for ThreadListSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.tag = Tag.objects.create(name='python')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        ThreadTags.objects.create(thread_id=self.thread, tag_id=self.tag)
    
    def test_thread_list_serialization(self):
        """Test thread list serialization."""
        serializer = ThreadListSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['id'], self.thread.id)
        self.assertEqual(data['title'], 'Test Thread')
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['category_id'], self.category.id)
        self.assertFalse(data['is_deleted'])
        self.assertIsNotNone(data['create_time'])
    
    def test_thread_list_author_display_name(self):
        """Test author display name in list view."""
        serializer = ThreadListSerializer(self.thread)
        data = serializer.data
        
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_thread_list_tags_flat(self):
        """Test tags_flat field in list view."""
        serializer = ThreadListSerializer(self.thread)
        data = serializer.data
        
        self.assertIn('python', data['tags_flat'])


class ReplySerializerTest(TestCase):
    """Test cases for ReplySerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        self.reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
    
    def test_reply_serialization(self):
        """Test reply serialization."""
        serializer = ReplySerializer(self.reply)
        data = serializer.data
        
        self.assertEqual(data['id'], self.reply.id)
        self.assertEqual(data['body'], 'Test reply')
        self.assertEqual(data['thread_id'], self.thread.id)
        self.assertEqual(data['user_id'], self.user.id)
        self.assertFalse(data['is_deleted'])
        self.assertIsNotNone(data['create_time'])
        self.assertIsNotNone(data['edit_time'])
    
    def test_reply_author_display_name_normal(self):
        """Test author display name for normal reply."""
        serializer = ReplySerializer(self.reply)
        data = serializer.data
        
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_reply_author_display_name_anonymous(self):
        """Test author display name for anonymous reply."""
        self.reply.is_anonymous = True
        self.reply.save()
        
        serializer = ReplySerializer(self.reply)
        data = serializer.data
        
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(data['author_display_name'], expected_name)
    
    def test_reply_author_display_name_admin_view(self):
        """Test author display name for admin view."""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_admin=True
        )
        
        self.reply.is_anonymous = True
        self.reply.save()
        
        # Mock request context with admin user
        mock_request = Mock()
        mock_request.user = admin_user
        
        serializer = ReplySerializer(self.reply, context={'request': mock_request})
        data = serializer.data
        
        # Admin should see real username even for anonymous replies
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_reply_like_count(self):
        """Test like count calculation."""
        # Create some likes
        ReplyLike.objects.create(
            user_id=self.user,
            reply_id=self.reply,
            status=True
        )
        
        serializer = ReplySerializer(self.reply)
        data = serializer.data
        
        self.assertEqual(data['like_count'], 1)
    
    def test_reply_creation(self):
        """Test reply creation."""
        data = {
            'thread_id': self.thread.id,
            'body': 'New reply',
            'is_anonymous': False
        }
        
        serializer = ReplySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        reply = serializer.save(user_id=self.user)
        
        self.assertEqual(reply.body, 'New reply')
        self.assertEqual(reply.thread_id, self.thread)
        self.assertFalse(reply.is_anonymous)
    
    def test_reply_creation_missing_thread_id(self):
        """Test reply creation without thread_id."""
        data = {
            'body': 'New reply'
        }
        
        serializer = ReplySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('thread_id', serializer.errors)
    
    def test_reply_creation_invalid_thread_id(self):
        """Test reply creation with invalid thread_id."""
        data = {
            'thread_id': 99999,  # Non-existent thread
            'body': 'New reply'
        }
        
        serializer = ReplySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('thread_id', serializer.errors)
    
    def test_reply_update_preserves_anonymity(self):
        """Test that reply update doesn't change anonymity."""
        self.reply.is_anonymous = True
        self.reply.save()
        
        data = {
            'body': 'Updated reply',
            'is_anonymous': False,  # This should be ignored
            'thread_id': 99999  # This should also be ignored
        }
        
        serializer = ReplySerializer(self.reply, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_reply = serializer.save()
        
        # Anonymity and thread_id should be preserved
        self.assertTrue(updated_reply.is_anonymous)
        self.assertEqual(updated_reply.thread_id, self.thread)


class ThreadLikeSerializerTest(TestCase):
    """Test cases for ThreadLikeSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        self.thread_like = ThreadLike.objects.create(
            user_id=self.user,
            thread_id=self.thread
        )
    
    def test_thread_like_serialization(self):
        """Test thread like serialization."""
        serializer = ThreadLikeSerializer(self.thread_like)
        data = serializer.data
        
        self.assertEqual(data['id'], self.thread_like.id)
        self.assertEqual(data['thread_id'], self.thread.id)
        self.assertEqual(data['thread_title'], 'Test Thread')
        self.assertTrue(data['status'])
        self.assertIsNotNone(data['create_time'])
    
    def test_thread_like_creation(self):
        """Test thread like creation."""
        data = {
            'thread_id': self.thread.id,
            'status': True
        }
        
        serializer = ThreadLikeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        like = serializer.save(user_id=self.user)
        
        self.assertEqual(like.thread_id, self.thread)
        self.assertTrue(like.status)


class ReplyLikeSerializerTest(TestCase):
    """Test cases for ReplyLikeSerializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        self.reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
        self.reply_like = ReplyLike.objects.create(
            user_id=self.user,
            reply_id=self.reply
        )
    
    def test_reply_like_serialization(self):
        """Test reply like serialization."""
        serializer = ReplyLikeSerializer(self.reply_like)
        data = serializer.data
        
        self.assertEqual(data['id'], self.reply_like.id)
        self.assertEqual(data['reply_id'], self.reply.id)
        self.assertTrue(data['status'])
        self.assertIsNotNone(data['create_time'])
    
    def test_reply_like_creation(self):
        """Test reply like creation."""
        data = {
            'reply_id': self.reply.id,
            'status': True
        }
        
        serializer = ReplyLikeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        like = serializer.save(user_id=self.user)
        
        self.assertEqual(like.reply_id, self.reply)
        self.assertTrue(like.status)


class SerializerValidationTest(TestCase):
    """Test cases for serializer validation edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
    
    def test_thread_title_length_validation(self):
        """Test thread title length validation."""
        data = {
            'title': 'x' * 121,  # Exceeds 120 character limit
            'body': 'Test body',
            'category_id': self.category.id
        }
        
        serializer = ThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
    
    def test_thread_body_length_validation(self):
        """Test thread body length validation."""
        data = {
            'title': 'Test title',
            'body': 'x' * 2001,  # Exceeds 2000 character limit
            'category_id': self.category.id
        }
        
        serializer = ThreadSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('body', serializer.errors)
    
    def test_tag_name_validation_edge_cases(self):
        """Test tag name validation edge cases."""
        # Test valid edge cases
        valid_names = ['a1', 'x' * 50, 'test-tag', 'test_tag', 'test123']
        
        for name in valid_names:
            data = {'name': name}
            serializer = TagCreateSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for valid name: {name}")
        
        # Test invalid edge cases
        invalid_names = ['a', 'x' * 51, 'test@tag', 'test tag', 'TEST-TAG']
        
        for name in invalid_names:
            data = {'name': name}
            serializer = TagCreateSerializer(data=data)
            self.assertFalse(serializer.is_valid(), f"Passed for invalid name: {name}")
    
    def test_serializer_field_read_only_behavior(self):
        """Test that read-only fields are properly handled."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        # Try to update read-only fields
        data = {
            'id': 99999,  # Should be ignored
            'user_id': 99999,  # Should be ignored
            'create_time': '2020-01-01T00:00:00Z',  # Should be ignored
            'title': 'Updated Title'  # Should be updated
        }
        
        serializer = ThreadSerializer(thread, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_thread = serializer.save()
        
        # Read-only fields should be unchanged
        self.assertEqual(updated_thread.id, thread.id)
        self.assertEqual(updated_thread.user_id, thread.user_id)
        self.assertEqual(updated_thread.create_time, thread.create_time)
        
        # Writable fields should be updated
        self.assertEqual(updated_thread.title, 'Updated Title')


class SerializerContextTest(TestCase):
    """Test cases for serializer context handling."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_admin=True
        )
        self.category = Category.objects.create(name='Academic')
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body',
            is_anonymous=True
        )
        self.reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply',
            is_anonymous=True
        )
    
    def test_thread_serializer_context_admin(self):
        """Test thread serializer with admin context."""
        mock_request = Mock()
        mock_request.user = self.admin_user
        
        serializer = ThreadSerializer(self.thread, context={'request': mock_request})
        data = serializer.data
        
        # Admin should see real username even for anonymous threads
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_thread_serializer_context_regular_user(self):
        """Test thread serializer with regular user context."""
        mock_request = Mock()
        mock_request.user = self.user
        
        serializer = ThreadSerializer(self.thread, context={'request': mock_request})
        data = serializer.data
        
        # Regular user should see anonymous display name
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(data['author_display_name'], expected_name)
    
    def test_reply_serializer_context_admin(self):
        """Test reply serializer with admin context."""
        mock_request = Mock()
        mock_request.user = self.admin_user
        
        serializer = ReplySerializer(self.reply, context={'request': mock_request})
        data = serializer.data
        
        # Admin should see real username even for anonymous replies
        self.assertEqual(data['author_display_name'], 'testuser')
    
    def test_reply_serializer_context_regular_user(self):
        """Test reply serializer with regular user context."""
        mock_request = Mock()
        mock_request.user = self.user
        
        serializer = ReplySerializer(self.reply, context={'request': mock_request})
        data = serializer.data
        
        # Regular user should see anonymous display name
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(data['author_display_name'], expected_name)
    
    def test_serializer_context_no_request(self):
        """Test serializer behavior without request context."""
        serializer = ThreadSerializer(self.thread)
        data = serializer.data
        
        # Without request context, should use model's get_author_display_name
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(data['author_display_name'], expected_name)
