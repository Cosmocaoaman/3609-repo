"""
Comprehensive test suite for API views.

This module contains tests for all API endpoints including authentication,
thread management, reply management, user management, and search functionality.
Tests cover both success and error scenarios, permissions, and edge cases.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
import json

from forum.models import (
    User, Category, Tag, Thread, Reply, ThreadTags, 
    ThreadLike, ReplyLike, ThreadView
)
from api.serializers import (
    UserSerializer, ThreadSerializer, ReplySerializer, TagSerializer,
    CategorySerializer, ThreadLikeSerializer, ReplyLikeSerializer
)


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
    
    @patch('api.views.email_service.send_otp_with_retry')
    def test_login_success(self, mock_send_otp):
        """Test successful login with OTP."""
        mock_send_otp.return_value = {'success': True, 'method': 'mailjet'}
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['mfa_required'])
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertEqual(response.data['email_status'], 'sent')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_missing_fields(self):
        """Test login with missing fields."""
        data = {'email': 'test@example.com'}
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_banned_user(self):
        """Test login attempt by banned user."""
        self.user.is_banned = True
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['banned'])
    
    def test_verify_otp_success(self):
        """Test successful OTP verification."""
        # Set OTP in cache
        cache.set(f'auth:otp:{self.user.id}', '123456', timeout=300)
        
        data = {
            'user_id': self.user.id,
            'otp': '123456'
        }
        
        response = self.client.post('/api/auth/verify-otp/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['user_id'], self.user.id)
    
    def test_verify_otp_invalid(self):
        """Test OTP verification with invalid OTP."""
        cache.set(f'auth:otp:{self.user.id}', '123456', timeout=300)
        
        data = {
            'user_id': self.user.id,
            'otp': '654321'
        }
        
        response = self.client.post('/api/auth/verify-otp/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired OTP."""
        data = {
            'user_id': self.user.id,
            'otp': '123456'
        }
        
        response = self.client.post('/api/auth/verify-otp/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_register_success(self):
        """Test successful user registration."""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'ComplexPass123!',
            'confirm_password': 'ComplexPass123!'
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        data = {
            'email': 'test@example.com',
            'username': 'newuser',
            'password': 'ComplexPass123!',
            'confirm_password': 'ComplexPass123!'
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch."""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'ComplexPass123!',
            'confirm_password': 'DifferentPass123!'
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_logout_success(self):
        """Test successful logout."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_whoami_authenticated(self):
        """Test whoami endpoint for authenticated user."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/auth/whoami/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['logged_in'])
        self.assertEqual(response.data['user_id'], self.user.id)
    
    def test_whoami_unauthenticated(self):
        """Test whoami endpoint for unauthenticated user."""
        response = self.client.get('/api/auth/whoami/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['logged_in'])


class ThreadAPITest(APITestCase):
    """Test cases for Thread API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
        self.tag = Tag.objects.create(name='python')
        
        self.thread_data = {
            'title': 'Test Thread',
            'body': 'This is a test thread body.',
            'category_id': self.category.id,
            'tag_names': ['python', 'django']
        }
    
    def test_create_thread_success(self):
        """Test successful thread creation."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/threads/', self.thread_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Thread')
        self.assertEqual(response.data['user_id'], self.user.id)
        
        # Verify thread was created in database
        thread = Thread.objects.get(id=response.data['id'])
        self.assertEqual(thread.title, 'Test Thread')
        self.assertEqual(thread.user_id, self.user)
    
    def test_create_thread_unauthenticated(self):
        """Test thread creation without authentication."""
        response = self.client.post('/api/threads/', self.thread_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_thread_anonymous(self):
        """Test creating anonymous thread."""
        self.client.force_authenticate(user=self.user)
        
        data = self.thread_data.copy()
        data['is_anonymous'] = True
        
        response = self.client.post('/api/threads/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_anonymous'])
    
    def test_list_threads(self):
        """Test listing threads."""
        # Create some test threads
        thread1 = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Thread 1',
            body='Body 1'
        )
        thread2 = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Thread 2',
            body='Body 2'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/threads/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_threads_with_tags(self):
        """Test listing threads filtered by tags."""
        # Create threads with different tags
        thread1 = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Python Thread',
            body='Body 1'
        )
        ThreadTags.objects.create(thread_id=thread1, tag_id=self.tag)
        
        thread2 = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Java Thread',
            body='Body 2'
        )
        java_tag = Tag.objects.create(name='java')
        ThreadTags.objects.create(thread_id=thread2, tag_id=java_tag)
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/threads/?tag=python')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Python Thread')
    
    def test_retrieve_thread(self):
        """Test retrieving a specific thread."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/threads/{thread.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Thread')
    
    def test_update_thread_author(self):
        """Test updating thread by author."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Original Title',
            body='Original body'
        )
        
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'title': 'Updated Title',
            'body': 'Updated body'
        }
        
        response = self.client.put(f'/api/threads/{thread.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')
        
        # Verify in database
        thread.refresh_from_db()
        self.assertEqual(thread.title, 'Updated Title')
    
    def test_update_thread_non_author(self):
        """Test updating thread by non-author."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Original Title',
            body='Original body'
        )
        
        self.client.force_authenticate(user=other_user)
        
        update_data = {
            'title': 'Updated Title',
            'body': 'Updated body'
        }
        
        response = self.client.put(f'/api/threads/{thread.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_thread_author(self):
        """Test deleting thread by author."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/threads/{thread.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        thread.refresh_from_db()
        self.assertTrue(thread.is_deleted)
    
    def test_delete_thread_admin(self):
        """Test deleting thread by admin."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/threads/{thread.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        thread.refresh_from_db()
        self.assertTrue(thread.is_deleted)
    
    def test_thread_like_toggle(self):
        """Test toggling thread like."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # First like
        response = self.client.post(f'/api/threads/{thread.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['like_count'], 1)
        
        # Second like (unlike)
        response = self.client.post(f'/api/threads/{thread.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])
        self.assertEqual(response.data['like_count'], 0)
    
    def test_thread_viewed(self):
        """Test recording thread view."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/threads/{thread.id}/viewed/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['ok'])
        
        # Verify view was recorded
        self.assertTrue(ThreadView.objects.filter(
            user_id=self.user,
            thread_id=thread
        ).exists())
    
    def test_thread_replies(self):
        """Test getting thread replies."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        reply1 = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Reply 1'
        )
        reply2 = Reply.objects.create(
            thread_id=thread,
            user_id=self.user,
            body='Reply 2'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/threads/{thread.id}/replies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_thread_restore_admin(self):
        """Test restoring thread by admin."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body',
            is_deleted=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/threads/{thread.id}/restore/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify restore
        thread.refresh_from_db()
        self.assertFalse(thread.is_deleted)
    
    def test_thread_restore_non_admin(self):
        """Test restoring thread by non-admin."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body',
            is_deleted=True
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/threads/{thread.id}/restore/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReplyAPITest(APITestCase):
    """Test cases for Reply API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
            body='Test body'
        )
        
        self.reply_data = {
            'thread_id': self.thread.id,
            'body': 'This is a test reply.'
        }
    
    def test_create_reply_success(self):
        """Test successful reply creation."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/replies/', self.reply_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['body'], 'This is a test reply.')
        self.assertEqual(response.data['thread_id'], self.thread.id)
        
        # Verify reply was created in database
        reply = Reply.objects.get(id=response.data['id'])
        self.assertEqual(reply.body, 'This is a test reply.')
        self.assertEqual(reply.thread_id, self.thread)
    
    def test_create_reply_unauthenticated(self):
        """Test reply creation without authentication."""
        response = self.client.post('/api/replies/', self.reply_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_reply_anonymous(self):
        """Test creating anonymous reply."""
        self.client.force_authenticate(user=self.user)
        
        data = self.reply_data.copy()
        data['is_anonymous'] = True
        
        response = self.client.post('/api/replies/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_anonymous'])
    
    def test_list_replies(self):
        """Test listing replies."""
        # Create some test replies
        reply1 = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Reply 1'
        )
        reply2 = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Reply 2'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/replies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_reply(self):
        """Test retrieving a specific reply."""
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/replies/{reply.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['body'], 'Test reply')
    
    def test_update_reply_author(self):
        """Test updating reply by author."""
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Original reply'
        )
        
        self.client.force_authenticate(user=self.user)
        
        update_data = {'body': 'Updated reply'}
        
        response = self.client.put(f'/api/replies/{reply.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['body'], 'Updated reply')
        
        # Verify in database
        reply.refresh_from_db()
        self.assertEqual(reply.body, 'Updated reply')
    
    def test_update_reply_non_author(self):
        """Test updating reply by non-author."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Original reply'
        )
        
        self.client.force_authenticate(user=other_user)
        
        update_data = {'body': 'Updated reply'}
        
        response = self.client.put(f'/api/replies/{reply.id}/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_reply_author(self):
        """Test deleting reply by author."""
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/replies/{reply.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete
        reply.refresh_from_db()
        self.assertTrue(reply.is_deleted)
    
    def test_reply_like_toggle(self):
        """Test toggling reply like."""
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # First like
        response = self.client.post(f'/api/replies/{reply.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['like_count'], 1)
        
        # Second like (unlike)
        response = self.client.post(f'/api/replies/{reply.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['liked'])
        self.assertEqual(response.data['like_count'], 0)
    
    def test_reply_restore_admin(self):
        """Test restoring reply by admin."""
        reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Test reply',
            is_deleted=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/replies/{reply.id}/restore/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify restore
        reply.refresh_from_db()
        self.assertFalse(reply.is_deleted)


class UserAPITest(APITestCase):
    """Test cases for User API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
    
    def test_list_users(self):
        """Test listing users."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_user(self):
        """Test retrieving a specific user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/users/{self.user.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_profile_success(self):
        """Test successful profile update."""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'username': 'newusername',
            'bio': 'This is my new bio'
        }
        
        response = self.client.post('/api/users/update_profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['username'], 'newusername')
        self.assertEqual(response.data['bio'], 'This is my new bio')
    
    def test_update_profile_duplicate_username(self):
        """Test profile update with duplicate username."""
        self.client.force_authenticate(user=self.user)
        
        data = {'username': 'admin'}  # Already exists
        
        response = self.client.post('/api/users/update_profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_update_profile_long_bio(self):
        """Test profile update with bio too long."""
        self.client.force_authenticate(user=self.user)
        
        data = {'bio': 'x' * 301}  # Exceeds 300 character limit
        
        response = self.client.post('/api/users/update_profile/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_user_stats(self):
        """Test getting user statistics."""
        # Create some content for the user
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
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/users/{self.user.id}/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['thread_count'], 1)
        self.assertEqual(response.data['reply_count'], 1)
    
    def test_user_history(self):
        """Test getting user browsing history."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        ThreadView.objects.create(
            user_id=self.user,
            thread_id=thread
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/users/{self.user.id}/history/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_user_likes(self):
        """Test getting user liked threads."""
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        ThreadLike.objects.create(
            user_id=self.user,
            thread_id=thread,
            status=True
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/users/{self.user.id}/likes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_ban_user_admin(self):
        """Test banning user by admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create some content for the user
        thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Test Thread',
            body='Test body'
        )
        
        response = self.client.post(f'/api/users/{self.user.id}/ban/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user is banned
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_banned)
        
        # Verify content is soft deleted
        thread.refresh_from_db()
        self.assertTrue(thread.is_deleted)
    
    def test_ban_user_non_admin(self):
        """Test banning user by non-admin."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(f'/api/users/{self.user.id}/ban/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unban_user_admin(self):
        """Test unbanning user by admin."""
        self.user.is_banned = True
        self.user.save()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/users/{self.user.id}/unban/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify user is unbanned
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_banned)


class TagAPITest(APITestCase):
    """Test cases for Tag API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
    
    def test_list_tags(self):
        """Test listing tags."""
        Tag.objects.create(name='python')
        Tag.objects.create(name='django')
        
        response = self.client.get('/api/tags/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_create_tag_admin(self):
        """Test creating tag by admin."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {'name': 'newtag'}
        
        response = self.client.post('/api/tags/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'newtag')
    
    def test_create_tag_non_admin(self):
        """Test creating tag by non-admin."""
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'newtag'}
        
        response = self.client.post('/api/tags/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_tag_invalid_name(self):
        """Test creating tag with invalid name."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {'name': 'a'}  # Too short
        
        response = self.client.post('/api/tags/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_disable_tag_admin(self):
        """Test disabling tag by admin."""
        tag = Tag.objects.create(name='testtag')
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/tags/{tag.name}/disable/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify tag is disabled
        tag.refresh_from_db()
        self.assertFalse(tag.is_active)
    
    def test_enable_tag_admin(self):
        """Test enabling tag by admin."""
        tag = Tag.objects.create(name='testtag', is_active=False)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/tags/{tag.name}/enable/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify tag is enabled
        tag.refresh_from_db()
        self.assertTrue(tag.is_active)


class CategoryAPITest(APITestCase):
    """Test cases for Category API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.category = Category.objects.create(name='Academic')
    
    def test_list_categories(self):
        """Test listing categories."""
        Category.objects.create(name='Social')
        
        response = self.client.get('/api/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_category(self):
        """Test retrieving a specific category."""
        response = self.client.get(f'/api/categories/{self.category.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Academic')


class SearchAPITest(APITestCase):
    """Test cases for Search API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Academic')
        
        self.thread = Thread.objects.create(
            user_id=self.user,
            category_id=self.category,
            title='Python Programming Guide',
            body='This is a comprehensive guide to Python programming.'
        )
        
        self.reply = Reply.objects.create(
            thread_id=self.thread,
            user_id=self.user,
            body='Great tutorial! Thanks for sharing.'
        )
    
    def test_search_threads(self):
        """Test searching threads."""
        response = self.client.get('/api/search/?q=python&type=threads')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_threads'], 1)
        self.assertEqual(len(response.data['threads']), 1)
    
    def test_search_replies(self):
        """Test searching replies."""
        response = self.client.get('/api/search/?q=tutorial&type=replies')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_replies'], 1)
        self.assertEqual(len(response.data['replies']), 1)
    
    def test_search_all(self):
        """Test searching all content."""
        response = self.client.get('/api/search/?q=python')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_results'], 2)
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        response = self.client.get('/api/search/?q=')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_search_long_query(self):
        """Test search with query too long."""
        long_query = 'x' * 101  # Exceeds 100 character limit
        
        response = self.client.get(f'/api/search/?q={long_query}')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_search_invalid_type(self):
        """Test search with invalid type."""
        response = self.client.get('/api/search/?q=python&type=invalid')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_search_invalid_sort(self):
        """Test search with invalid sort order."""
        response = self.client.get('/api/search/?q=python&sort=invalid')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class AnonymousModeAPITest(APITestCase):
    """Test cases for Anonymous Mode API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_toggle_anonymous_mode_enable(self):
        """Test enabling anonymous mode."""
        self.client.force_authenticate(user=self.user)
        
        data = {'is_anonymous': True}
        response = self.client.post('/api/auth/toggle-anonymous/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['is_anonymous'])
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_anonymous)
    
    def test_toggle_anonymous_mode_disable(self):
        """Test disabling anonymous mode."""
        self.user.is_anonymous = True
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        
        data = {'is_anonymous': False}
        response = self.client.post('/api/auth/toggle-anonymous/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['is_anonymous'])
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_anonymous)
    
    def test_toggle_anonymous_mode_unauthenticated(self):
        """Test toggling anonymous mode without authentication."""
        data = {'is_anonymous': True}
        response = self.client.post('/api/auth/toggle-anonymous/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class APIPermissionTest(APITestCase):
    """Test cases for API permissions and access control."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
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
            body='Test body'
        )
    
    def test_unauthenticated_access_restricted_endpoints(self):
        """Test that unauthenticated users cannot access restricted endpoints."""
        restricted_endpoints = [
            '/api/threads/',
            '/api/replies/',
            '/api/users/',
            '/api/auth/logout/',
            '/api/auth/toggle-anonymous/'
        ]
        
        for endpoint in restricted_endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_unauthenticated_access_public_endpoints(self):
        """Test that unauthenticated users can access public endpoints."""
        public_endpoints = [
            '/api/categories/',
            '/api/tags/',
            '/api/auth/whoami/',
            '/api/search/?q=test'
        ]
        
        for endpoint in public_endpoints:
            response = self.client.get(endpoint)
            self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_only_endpoints(self):
        """Test that only admin users can access admin-only endpoints."""
        admin_endpoints = [
            f'/api/threads/{self.thread.id}/restore/',
            f'/api/replies/1/restore/',
            f'/api/users/{self.user.id}/ban/',
            f'/api/users/{self.user.id}/unban/',
            '/api/tags/',
        ]
        
        # Test with regular user
        self.client.force_authenticate(user=self.user)
        for endpoint in admin_endpoints:
            response = self.client.post(endpoint)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin user
        self.client.force_authenticate(user=self.admin_user)
        for endpoint in admin_endpoints:
            # These should not return 403, but may return other status codes
            response = self.client.post(endpoint)
            self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class APIErrorHandlingTest(APITestCase):
    """Test cases for API error handling and edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_nonexistent_thread(self):
        """Test accessing nonexistent thread."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/threads/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_nonexistent_reply(self):
        """Test accessing nonexistent reply."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/replies/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_nonexistent_user(self):
        """Test accessing nonexistent user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_json_data(self):
        """Test sending invalid JSON data."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(
            '/api/threads/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_missing_required_fields(self):
        """Test missing required fields in requests."""
        self.client.force_authenticate(user=self.user)
        
        # Missing title and body for thread creation
        data = {'category_id': 1}
        response = self.client.post('/api/threads/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_rate_limiting_login(self):
        """Test rate limiting for login attempts."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        # Make multiple failed login attempts
        for _ in range(6):  # Exceed the limit of 5
            response = self.client.post('/api/auth/login/', data)
        
        # Should be rate limited
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)