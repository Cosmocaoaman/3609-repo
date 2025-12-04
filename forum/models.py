"""
Database models for the Jacaranda Talk forum application.

This module defines all database models based on the previous ERD design.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from .email_service import email_service


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Provides user authentication and profile information.
    Supports both normal users and admin users.
    Users can switch between normal and anonymous modes.
    """
    username = models.CharField(max_length=50, unique=True, null=False, help_text="User's display name/nickname")
    email = models.TextField(unique=True, null=False, help_text="Encrypted email address")
    is_anonymous = models.BooleanField(default=False, help_text="User's current posting mode (normal/anonymous)")
    is_admin = models.BooleanField(default=False, help_text="Designates whether this user is an admin")
    is_banned = models.BooleanField(default=False, help_text="Designates whether this user is banned (soft deleted)")
    bio = models.TextField(max_length=300, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'
    
    def __str__(self):
        return self.username
    
    def get_email(self):
        """Return plain email address (no encryption)."""
        return self.email
    
    def set_email(self, email):
        """Set plain email address (no encryption)."""
        self.email = email
    
    def save(self, *args, **kwargs):
        """Standard save without email encryption."""
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    Category model for organizing threads.
    
    Represents different discussion categories (e.g., Academic, Social, Events).
    Each thread must belong to exactly one category.
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True, null=False)

    class Meta:
        db_table = 'category'
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('forum:category_threads', kwargs={'category_id': self.id})


class Tag(models.Model):
    """
    Tag model for categorizing threads.
    
    Tags help users find content by topics of interest.
    Multiple tags can be associated with a single thread.
    """
    name = models.CharField(max_length=100, primary_key=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tag'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('forum:tag_detail', kwargs={'tag_name': self.name})


class Thread(models.Model):
    """
    Thread model representing discussion topics.
    
    Each thread contains a title, body text, and belongs to a category.
    Threads can have multiple tags and inherit anonymous status from user.
    """
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')
    title = models.CharField(max_length=120, null=False)
    body = models.TextField(max_length=2000, null=False)
    is_anonymous = models.BooleanField(default=False, help_text='Whether this thread was posted anonymously')
    is_deleted = models.BooleanField(default=False, help_text='Soft delete flag')
    create_time = models.DateTimeField(auto_now_add=True)
    edit_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'thread'
        ordering = ['-create_time']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('forum:thread_detail', kwargs={'thread_id': self.id})
    
    def get_author_display_name(self):
        """Get display name for author (anonymous or username)."""
        if self.is_anonymous:
            return f"Anonymous#{self.user_id.id}"
        return self.user_id.username
    
    def soft_delete(self):
        """Soft delete thread"""
        self.is_deleted = True
        self.save()
        # Cascade delete related replies
        Reply.objects.filter(thread_id=self).update(is_deleted=True)
    
    def restore(self):
        """Restore soft deleted thread"""
        self.is_deleted = False
        self.save()
        # Restore related replies
        Reply.objects.filter(thread_id=self).update(is_deleted=False)


class ThreadTags(models.Model):
    """
    Junction table for thread-tag relationships.
    
    Represents the many-to-many relationship between threads and tags.
    """
    thread_id = models.ForeignKey(Thread, on_delete=models.CASCADE, db_column='thread_id')
    tag_id = models.ForeignKey(Tag, on_delete=models.CASCADE, db_column='tag_id')

    class Meta:
        db_table = 'thread_tags'
        unique_together = ('thread_id', 'tag_id')
    
    def __str__(self):
        return f"'{self.thread_id.title}' tagged with '{self.tag_id.name}'"


class Reply(models.Model):
    """
    Reply model for responses to threads.
    
    Each reply belongs to exactly one thread and inherits anonymous status from user.
    """
    id = models.AutoField(primary_key=True)
    thread_id = models.ForeignKey(Thread, on_delete=models.CASCADE, db_column='thread_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    body = models.TextField(null=False)
    is_anonymous = models.BooleanField(default=False, help_text='Whether this reply was posted anonymously')
    like_count = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False, help_text='Soft delete flag')
    create_time = models.DateTimeField(auto_now_add=True)
    edit_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reply'
        ordering = ['create_time']
        verbose_name_plural = "Replies"
    
    def __str__(self):
        return f"Reply to '{self.thread_id.title}' by {self.get_author_display_name()}"
    
    def get_author_display_name(self):
        """Get display name for author (anonymous or username)."""
        if self.is_anonymous:
            return f"Anonymous#{self.user_id.id}"
        return self.user_id.username
    
    def soft_delete(self):
        """Soft delete reply"""
        self.is_deleted = True
        self.save()
    
    def restore(self):
        """Restore soft deleted reply"""
        self.is_deleted = False
        self.save()


class ThreadLike(models.Model):
    """
    Junction table for user likes on threads.
    
    Represents the many-to-many relationship between users and threads
    with additional metadata (timestamps).
    """
    id = models.AutoField(primary_key=True)
    thread_id = models.ForeignKey(Thread, on_delete=models.CASCADE, db_column='thread_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    status = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'thread_like'
        unique_together = ('thread_id', 'user_id')
        ordering = ['-create_time']
    
    def __str__(self):
        return f"{self.user_id.username} likes '{self.thread_id.title}'"


class ReplyLike(models.Model):
    """
    Junction table for user likes on replies.
    
    Represents the many-to-many relationship between users and replies
    with additional metadata (timestamps).
    """
    id = models.AutoField(primary_key=True)
    reply_id = models.ForeignKey(Reply, on_delete=models.CASCADE, db_column='reply_id')
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    status = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reply_like'
        unique_together = ('reply_id', 'user_id')
        ordering = ['-create_time']
    
    def __str__(self):
        return f"{self.user_id.username} likes reply to '{self.reply_id.thread_id.title}'"



class ThreadView(models.Model):
    """
    Record of a user viewing a thread.
    Only the latest view per (user, thread) is kept (we upsert on write).
    """
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    thread_id = models.ForeignKey(Thread, on_delete=models.CASCADE, db_column='thread_id')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'thread_view'
        unique_together = ('user_id', 'thread_id')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user_id.username} viewed '{self.thread_id.title}' at {self.viewed_at}"