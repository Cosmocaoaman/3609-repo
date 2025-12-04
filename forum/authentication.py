"""
Custom authentication backends for the Jacaranda Talk forum application.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to login using their email address.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate using email or username."""
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return
        
        try:
            # First try to find user by email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # If not found by email, try by username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a non-existing user
                User().set_password(password)
                return
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False or is_banned=True.
        """
        # Check Django's default is_active field
        if not getattr(user, 'is_active', True):
            return False
        
        # Check our custom is_banned field
        if getattr(user, 'is_banned', False):
            return False
        
        return True