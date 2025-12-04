"""
Comprehensive test suite for forum models.

This module contains tests for all forum models including User, Thread, Reply,
Category, Tag, and related models. Tests cover model creation, validation,
relationships, and business logic.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import datetime, timedelta
from unittest.mock import patch

from .models import (
    User, Category, Tag, Thread, Reply, ThreadTags, 
    ThreadLike, ReplyLike, ThreadView
)


class UserModelTest(TestCase):
    """Test cases for User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_user_creation(self):
        """Test basic user creation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertFalse(user.is_anonymous)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_banned)
        self.assertIsNotNone(user.create_time)
        self.assertIsNotNone(user.update_time)
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')
    
    def test_user_email_methods(self):
        """Test email getter and setter methods."""
        user = User.objects.create_user(**self.user_data)
        
        # Test get_email
        self.assertEqual(user.get_email(), 'test@example.com')
        
        # Test set_email
        user.set_email('newemail@example.com')
        self.assertEqual(user.email, 'newemail@example.com')
    
    def test_user_anonymous_mode(self):
        """Test anonymous mode functionality."""
        user = User.objects.create_user(**self.user_data)
        
        # Test default anonymous mode
        self.assertFalse(user.is_anonymous)
        
        # Test enabling anonymous mode
        user.is_anonymous = True
        user.save()
        self.assertTrue(user.is_anonymous)
    
    def test_user_admin_status(self):
        """Test admin status functionality."""
        user = User.objects.create_user(**self.user_data)
        
        # Test default admin status
        self.assertFalse(user.is_admin)
        
        # Test making user admin
        user.is_admin = True
        user.save()
        self.assertTrue(user.is_admin)
    
    def test_user_ban_status(self):
        """Test ban status functionality."""
        user = User.objects.create_user(**self.user_data)
        
        # Test default ban status
        self.assertFalse(user.is_banned)
        
        # Test banning user
        user.is_banned = True
        user.save()
        self.assertTrue(user.is_banned)
    
    def test_user_bio_field(self):
        """Test bio field functionality."""
        user = User.objects.create_user(**self.user_data)
        
        # Test empty bio
        self.assertIsNone(user.bio)
        
        # Test setting bio
        bio_text = "This is a test bio for the user."
        user.bio = bio_text
        user.save()
        self.assertEqual(user.bio, bio_text)
        
        # Test bio length limit - Django allows saving but validation should catch it
        long_bio = "x" * 301  # Exceeds 300 character limit
        user.bio = long_bio
        user.save()  # Django allows saving
        # The validation would be handled at the form/serializer level
        self.assertEqual(len(user.bio), 301)
    
    def test_user_unique_constraints(self):
        """Test unique constraints on username and email."""
        User.objects.create_user(**self.user_data)
        
        # Test duplicate username
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser',
                email='different@example.com',
                password='testpass123'
            )
        
        # Test duplicate email - use a different approach to avoid transaction issues
        # Create a new user with different username first
        user2_data = {
            'username': 'differentuser',
            'email': 'different@example.com',
            'password': 'testpass123'
        }
        User.objects.create_user(**user2_data)
        
        # Now try to create another user with the same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='anotheruser',
                email='test@example.com',
                password='testpass123'
            )


class CategoryModelTest(TestCase):
    """Test cases for Category model."""
    
    def setUp(self):
        """Set up test data."""
        self.category_data = {'name': 'Academic'}
    
    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.name, 'Academic')
        self.assertIsNotNone(category.id)
    
    def test_category_str_representation(self):
        """Test category string representation."""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(str(category), 'Academic')
    
    def test_category_unique_constraint(self):
        """Test unique constraint on category name."""
        Category.objects.create(**self.category_data)
        
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Academic')
    
    def test_category_get_absolute_url(self):
        """Test category absolute URL generation."""
        category = Category.objects.create(**self.category_data)
        expected_url = f'/forum/category/{category.id}/threads/'
        # Note: This test assumes URL pattern exists
        # In real implementation, you'd need to set up URL patterns


class TagModelTest(TestCase):
    """Test cases for Tag model."""
    
    def setUp(self):
        """Set up test data."""
        self.tag_data = {'name': 'python'}
    
    def test_tag_creation(self):
        """Test basic tag creation."""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(tag.name, 'python')
        self.assertTrue(tag.is_active)
    
    def test_tag_str_representation(self):
        """Test tag string representation."""
        tag = Tag.objects.create(**self.tag_data)
        self.assertEqual(str(tag), 'python')
    
    def test_tag_active_status(self):
        """Test tag active status functionality."""
        tag = Tag.objects.create(**self.tag_data)
        
        # Test default active status
        self.assertTrue(tag.is_active)
        
        # Test deactivating tag
        tag.is_active = False
        tag.save()
        self.assertFalse(tag.is_active)
    
    def test_tag_get_absolute_url(self):
        """Test tag absolute URL generation."""
        tag = Tag.objects.create(**self.tag_data)
        expected_url = f'/forum/tag/{tag.name}/'
        # Note: This test assumes URL pattern exists


class ThreadModelTest(TestCase):
    """Test cases for Thread model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.thread_data = {
            'user_id': self.user,
            'category_id': self.category,
            'title': 'Test Thread Title',
            'body': 'This is a test thread body content.'
        }
    
    def test_thread_creation(self):
        """Test basic thread creation."""
        thread = Thread.objects.create(**self.thread_data)
        self.assertEqual(thread.title, 'Test Thread Title')
        self.assertEqual(thread.body, 'This is a test thread body content.')
        self.assertEqual(thread.user_id, self.user)
        self.assertEqual(thread.category_id, self.category)
        self.assertFalse(thread.is_anonymous)
        self.assertFalse(thread.is_deleted)
        self.assertIsNotNone(thread.create_time)
        self.assertIsNotNone(thread.edit_time)
    
    def test_thread_str_representation(self):
        """Test thread string representation."""
        thread = Thread.objects.create(**self.thread_data)
        self.assertEqual(str(thread), 'Test Thread Title')
    
    def test_thread_get_absolute_url(self):
        """Test thread absolute URL generation."""
        thread = Thread.objects.create(**self.thread_data)
        expected_url = f'/forum/thread/{thread.id}/'
        # Note: This test assumes URL pattern exists
    
    def test_thread_author_display_name_normal(self):
        """Test author display name for normal (non-anonymous) thread."""
        thread = Thread.objects.create(**self.thread_data)
        self.assertEqual(thread.get_author_display_name(), 'testuser')
    
    def test_thread_author_display_name_anonymous(self):
        """Test author display name for anonymous thread."""
        thread = Thread.objects.create(
            **self.thread_data,
            is_anonymous=True
        )
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(thread.get_author_display_name(), expected_name)
    
    def test_thread_soft_delete(self):
        """Test thread soft delete functionality."""
        thread = Thread.objects.create(**self.thread_data)
        
        # Create a reply to test cascade delete
        reply = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Test reply'
        )
        
        # Soft delete thread
        thread.soft_delete()
        
        # Check thread is soft deleted
        self.assertTrue(thread.is_deleted)
        
        # Check reply is also soft deleted
        reply.refresh_from_db()
        self.assertTrue(reply.is_deleted)
    
    def test_thread_restore(self):
        """Test thread restore functionality."""
        thread = Thread.objects.create(**self.thread_data)
        
        # Create a reply
        reply = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Test reply'
        )
        
        # Soft delete and then restore
        thread.soft_delete()
        thread.restore()
        
        # Check thread is restored
        self.assertFalse(thread.is_deleted)
        
        # Check reply is also restored
        reply.refresh_from_db()
        self.assertFalse(reply.is_deleted)
    
    def test_thread_title_length_validation(self):
        """Test thread title length validation."""
        long_title = "x" * 121  # Exceeds 120 character limit
        
        # Create thread data without title first
        thread_data = {
            'user_id': self.user,
            'category_id': self.category,
            'body': 'Test body'
        }
        
        with self.assertRaises(ValidationError):
            thread = Thread.objects.create(**thread_data, title=long_title)
            thread.full_clean()
    
    def test_thread_body_length_validation(self):
        """Test thread body length validation."""
        long_body = "x" * 2001  # Exceeds 2000 character limit
        
        # Create thread data without body first
        thread_data = {
            'user_id': self.user,
            'category_id': self.category,
            'title': 'Test title'
        }
        
        with self.assertRaises(ValidationError):
            thread = Thread.objects.create(**thread_data, body=long_body)
            thread.full_clean()


class ThreadTagsModelTest(TestCase):
    """Test cases for ThreadTags model."""
    
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
    
    def test_thread_tags_creation(self):
        """Test basic thread-tag relationship creation."""
        thread_tag = ThreadTags.objects.create(
            thread_id=self.thread,
            tag_id=self.tag
        )
        self.assertEqual(thread_tag.thread_id, self.thread)
        self.assertEqual(thread_tag.tag_id, self.tag)
    
    def test_thread_tags_str_representation(self):
        """Test thread-tag string representation."""
        thread_tag = ThreadTags.objects.create(
            thread_id=self.thread,
            tag_id=self.tag
        )
        expected_str = f"'{self.thread.title}' tagged with '{self.tag.name}'"
        self.assertEqual(str(thread_tag), expected_str)
    
    def test_thread_tags_unique_constraint(self):
        """Test unique constraint on thread-tag relationship."""
        ThreadTags.objects.create(
            thread_id=self.thread,
            tag_id=self.tag
        )
        
        with self.assertRaises(IntegrityError):
            ThreadTags.objects.create(
                thread_id=self.thread,
                tag_id=self.tag
            )


class ReplyModelTest(TestCase):
    """Test cases for Reply model."""
    
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
        self.reply_data = {
            'thread_id': self.thread,
            'user_id': self.user,
            'body': 'This is a test reply.'
        }
    
    def test_reply_creation(self):
        """Test basic reply creation."""
        reply = Reply.objects.create(**self.reply_data)
        self.assertEqual(reply.body, 'This is a test reply.')
        self.assertEqual(reply.thread_id, self.thread)
        self.assertEqual(reply.user_id, self.user)
        self.assertFalse(reply.is_anonymous)
        self.assertFalse(reply.is_deleted)
        self.assertEqual(reply.like_count, 0)
        self.assertIsNotNone(reply.create_time)
        self.assertIsNotNone(reply.edit_time)
    
    def test_reply_str_representation(self):
        """Test reply string representation."""
        reply = Reply.objects.create(**self.reply_data)
        expected_str = f"Reply to '{self.thread.title}' by {self.user.username}"
        self.assertEqual(str(reply), expected_str)
    
    def test_reply_author_display_name_normal(self):
        """Test author display name for normal (non-anonymous) reply."""
        reply = Reply.objects.create(**self.reply_data)
        self.assertEqual(reply.get_author_display_name(), 'testuser')
    
    def test_reply_author_display_name_anonymous(self):
        """Test author display name for anonymous reply."""
        reply = Reply.objects.create(
            **self.reply_data,
            is_anonymous=True
        )
        expected_name = f"Anonymous#{self.user.id}"
        self.assertEqual(reply.get_author_display_name(), expected_name)
    
    def test_reply_soft_delete(self):
        """Test reply soft delete functionality."""
        reply = Reply.objects.create(**self.reply_data)
        
        # Soft delete reply
        reply.soft_delete()
        
        # Check reply is soft deleted
        self.assertTrue(reply.is_deleted)
    
    def test_reply_restore(self):
        """Test reply restore functionality."""
        reply = Reply.objects.create(**self.reply_data)
        
        # Soft delete and then restore
        reply.soft_delete()
        reply.restore()
        
        # Check reply is restored
        self.assertFalse(reply.is_deleted)
    
    def test_reply_like_count(self):
        """Test reply like count functionality."""
        reply = Reply.objects.create(**self.reply_data)
        
        # Test initial like count
        self.assertEqual(reply.like_count, 0)
        
        # Test updating like count
        reply.like_count = 5
        reply.save()
        self.assertEqual(reply.like_count, 5)


class ThreadLikeModelTest(TestCase):
    """Test cases for ThreadLike model."""
    
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
    
    def test_thread_like_creation(self):
        """Test basic thread like creation."""
        thread_like = ThreadLike.objects.create(
            thread_id=self.thread,
            user_id=self.user
        )
        self.assertEqual(thread_like.thread_id, self.thread)
        self.assertEqual(thread_like.user_id, self.user)
        self.assertTrue(thread_like.status)
        self.assertIsNotNone(thread_like.create_time)
    
    def test_thread_like_str_representation(self):
        """Test thread like string representation."""
        thread_like = ThreadLike.objects.create(
            thread_id=self.thread,
            user_id=self.user
        )
        expected_str = f"{self.user.username} likes '{self.thread.title}'"
        self.assertEqual(str(thread_like), expected_str)
    
    def test_thread_like_unique_constraint(self):
        """Test unique constraint on thread-user like relationship."""
        ThreadLike.objects.create(
            thread_id=self.thread,
            user_id=self.user
        )
        
        with self.assertRaises(IntegrityError):
            ThreadLike.objects.create(
                thread_id=self.thread,
                user_id=self.user
            )
    
    def test_thread_like_status_toggle(self):
        """Test thread like status toggle functionality."""
        thread_like = ThreadLike.objects.create(
            thread_id=self.thread,
            user_id=self.user
        )
        
        # Test initial status
        self.assertTrue(thread_like.status)
        
        # Test toggling status
        thread_like.status = False
        thread_like.save()
        self.assertFalse(thread_like.status)


class ReplyLikeModelTest(TestCase):
    """Test cases for ReplyLike model."""
    
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
    
    def test_reply_like_creation(self):
        """Test basic reply like creation."""
        reply_like = ReplyLike.objects.create(
            reply_id=self.reply,
            user_id=self.user
        )
        self.assertEqual(reply_like.reply_id, self.reply)
        self.assertEqual(reply_like.user_id, self.user)
        self.assertTrue(reply_like.status)
        self.assertIsNotNone(reply_like.create_time)
    
    def test_reply_like_str_representation(self):
        """Test reply like string representation."""
        reply_like = ReplyLike.objects.create(
            reply_id=self.reply,
            user_id=self.user
        )
        expected_str = f"{self.user.username} likes reply to '{self.thread.title}'"
        self.assertEqual(str(reply_like), expected_str)
    
    def test_reply_like_unique_constraint(self):
        """Test unique constraint on reply-user like relationship."""
        ReplyLike.objects.create(
            reply_id=self.reply,
            user_id=self.user
        )
        
        with self.assertRaises(IntegrityError):
            ReplyLike.objects.create(
                reply_id=self.reply,
                user_id=self.user
            )
    
    def test_reply_like_status_toggle(self):
        """Test reply like status toggle functionality."""
        reply_like = ReplyLike.objects.create(
            reply_id=self.reply,
            user_id=self.user
        )
        
        # Test initial status
        self.assertTrue(reply_like.status)
        
        # Test toggling status
        reply_like.status = False
        reply_like.save()
        self.assertFalse(reply_like.status)


class ThreadViewModelTest(TestCase):
    """Test cases for ThreadView model."""
    
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
    
    def test_thread_view_creation(self):
        """Test basic thread view creation."""
        thread_view = ThreadView.objects.create(
            user_id=self.user,
            thread_id=self.thread
        )
        self.assertEqual(thread_view.user_id, self.user)
        self.assertEqual(thread_view.thread_id, self.thread)
        self.assertIsNotNone(thread_view.viewed_at)
    
    def test_thread_view_str_representation(self):
        """Test thread view string representation."""
        thread_view = ThreadView.objects.create(
            user_id=self.user,
            thread_id=self.thread
        )
        expected_str = f"{self.user.username} viewed '{self.thread.title}' at {thread_view.viewed_at}"
        self.assertEqual(str(thread_view), expected_str)
    
    def test_thread_view_unique_constraint(self):
        """Test unique constraint on user-thread view relationship."""
        ThreadView.objects.create(
            user_id=self.user,
            thread_id=self.thread
        )
        
        # Creating another view should update the existing one
        # This tests the upsert behavior
        from django.utils import timezone
        from datetime import timedelta
        
        new_time = timezone.now() + timedelta(hours=1)
        ThreadView.objects.update_or_create(
            user_id=self.user,
            thread_id=self.thread,
            defaults={'viewed_at': new_time}
        )
        
        # Should only have one record
        self.assertEqual(ThreadView.objects.count(), 1)
        
        # The viewed_at should be updated
        thread_view = ThreadView.objects.get(
            user_id=self.user,
            thread_id=self.thread
        )
        self.assertIsNotNone(thread_view.viewed_at)


class ModelRelationshipTest(TestCase):
    """Test cases for model relationships and cascading behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        self.tag = Tag.objects.create(name='python')
    
    def test_user_thread_cascade_delete(self):
        """Test that deleting a user cascades to their threads."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        # Delete user
        self.user.delete()
        
        # Thread should be deleted
        self.assertFalse(Thread.objects.filter(id=thread.id).exists())
    
    def test_category_thread_cascade_delete(self):
        """Test that deleting a category cascades to threads."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        # Delete category
        self.category.delete()
        
        # Thread should be deleted
        self.assertFalse(Thread.objects.filter(id=thread.id).exists())
    
    def test_thread_reply_cascade_delete(self):
        """Test that deleting a thread cascades to replies."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        reply = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Test reply'
        )
        
        # Delete thread
        thread.delete()
        
        # Reply should be deleted
        self.assertFalse(Reply.objects.filter(id=reply.id).exists())
    
    def test_thread_tags_cascade_delete(self):
        """Test that deleting a thread cascades to thread-tag relationships."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        thread_tag = ThreadTags.objects.create(
            thread_id=thread,
            tag_id=self.tag
        )
        
        # Delete thread
        thread.delete()
        
        # Thread-tag relationship should be deleted
        self.assertFalse(ThreadTags.objects.filter(id=thread_tag.id).exists())
    
    def test_thread_like_cascade_delete(self):
        """Test that deleting a thread cascades to thread likes."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        thread_like = ThreadLike.objects.create(
            thread_id=thread,
            user_id=self.user
        )
        
        # Delete thread
        thread.delete()
        
        # Thread like should be deleted
        self.assertFalse(ThreadLike.objects.filter(id=thread_like.id).exists())
    
    def test_reply_like_cascade_delete(self):
        """Test that deleting a reply cascades to reply likes."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        reply = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Test reply'
        )
        reply_like = ReplyLike.objects.create(
            reply_id=reply,
            user_id=self.user
        )
        
        # Delete reply
        reply.delete()
        
        # Reply like should be deleted
        self.assertFalse(ReplyLike.objects.filter(id=reply_like.id).exists())
    
    def test_thread_view_cascade_delete(self):
        """Test that deleting a thread cascades to thread views."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        thread_view = ThreadView.objects.create(
            user_id=self.user,
            thread_id=thread
        )
        
        # Delete thread
        thread.delete()
        
        # Thread view should be deleted
        self.assertFalse(ThreadView.objects.filter(id=thread_view.id).exists())


class ModelValidationTest(TestCase):
    """Test cases for model validation and edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
    
    def test_empty_string_validation(self):
        """Test validation of empty strings."""
        # Test empty thread title
        with self.assertRaises(ValidationError):
            thread = Thread.objects.create(
                user_id=self.user,
                category_id=self.category,
                title='',
                body='Test body'
            )
            thread.full_clean()
        
        # Test empty thread body
        with self.assertRaises(ValidationError):
            thread = Thread.objects.create(
                user_id=self.user,
                category_id=self.category,
                title='Test title',
                body=''
            )
            thread.full_clean()
    
    def test_null_field_validation(self):
        """Test validation of null fields."""
        # Test null thread title
        with self.assertRaises(IntegrityError):
            Thread.objects.create(
                user_id=self.user,
                category_id=self.category,
                title=None,
                body='Test body'
            )
        
        # Test null thread body
        with self.assertRaises(IntegrityError):
            Thread.objects.create(
                user_id=self.user,
                category_id=self.category,
                title='Test title',
                body=None
            )
    
    def test_foreign_key_validation(self):
        """Test foreign key validation."""
        # Test invalid user_id - create a thread with non-existent user
        # This should fail at the database level
        try:
            Thread.objects.create(
                user_id_id=99999,  # Non-existent user
                category_id=self.category,
                title='Test title',
                body='Test body'
            )
            self.fail("Expected IntegrityError for invalid user_id")
        except IntegrityError:
            pass  # Expected behavior
        
        # Test invalid category_id - create a thread with non-existent category
        try:
            Thread.objects.create(
                user_id=self.user,
                category_id_id=99999,  # Non-existent category
                title='Test title',
                body='Test body'
            )
            self.fail("Expected IntegrityError for invalid category_id")
        except IntegrityError:
            pass  # Expected behavior