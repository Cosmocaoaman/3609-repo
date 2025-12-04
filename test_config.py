"""
Test configuration for backend testing.

This module provides test-specific settings and utilities
to ensure consistent test environment setup.
"""

import os
import tempfile
from django.conf import settings

# Test-specific settings
TEST_SETTINGS = {
    'DEBUG': False,
    'SECRET_KEY': 'test-secret-key-for-testing-only',
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    },
    'EMAIL_BACKEND': 'django.core.mail.backends.locmem.EmailBackend',
    'PASSWORD_HASHERS': [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ],
    'LOGGING': {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'WARNING',
            },
        },
    },
    'MEDIA_ROOT': tempfile.mkdtemp(),
    'STATIC_ROOT': tempfile.mkdtemp(),
}

def setup_test_environment():
    """Setup test environment with test-specific settings."""
    # Update settings with test configuration
    for key, value in TEST_SETTINGS.items():
        setattr(settings, key, value)
    
    # Ensure test database is used
    settings.DATABASES['default']['NAME'] = ':memory:'
    
    return settings

def create_test_data():
    """Create test data for testing."""
    from forum.models import User, Category, Tag, Thread, Reply
    
    # Create test users
    test_user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    admin_user = User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        is_admin=True
    )
    
    # Create test categories
    academic_category = Category.objects.create(name='Academic')
    social_category = Category.objects.create(name='Social')
    
    # Create test tags
    python_tag = Tag.objects.create(name='python')
    django_tag = Tag.objects.create(name='django')
    inactive_tag = Tag.objects.create(name='inactive', is_active=False)
    
    # Create test threads
    thread1 = Thread.objects.create(
        user_id=test_user,
        category_id=academic_category,
        title='Python Programming Guide',
        body='This is a comprehensive guide to Python programming.'
    )
    
    thread2 = Thread.objects.create(
        user_id=test_user,
        category_id=social_category,
        title='Social Discussion',
        body='This is a social discussion thread.',
        is_anonymous=True
    )
    
    # Create test replies
    reply1 = Reply.objects.create(
        thread_id=thread1,
        user_id=test_user,
        body='Great tutorial! Thanks for sharing.'
    )
    
    reply2 = Reply.objects.create(
        thread_id=thread1,
        user_id=admin_user,
        body='This is very helpful.',
        is_anonymous=True
    )
    
    return {
        'users': [test_user, admin_user],
        'categories': [academic_category, social_category],
        'tags': [python_tag, django_tag, inactive_tag],
        'threads': [thread1, thread2],
        'replies': [reply1, reply2]
    }

def cleanup_test_data():
    """Clean up test data after tests."""
    from django.core.cache import cache
    cache.clear()
    
    # Clean up temporary directories
    import shutil
    if hasattr(settings, 'MEDIA_ROOT'):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    if hasattr(settings, 'STATIC_ROOT'):
        shutil.rmtree(settings.STATIC_ROOT, ignore_errors=True)
