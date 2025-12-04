"""
Email service module for Jacaranda Talk forum.

This module provides email sending functionality using Mailjet API
with fallback to Django's file-based email backend for development.
"""

import logging
import time
import base64
from typing import Dict, Any
from django.conf import settings
from django.core.mail import send_mail
from django.core.cache import cache
from cryptography.fernet import Fernet
import requests

logger = logging.getLogger(__name__)


class EmailEncryption:
    """Handle email encryption and decryption."""
    
    def __init__(self):
        # Generate or retrieve encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from Django settings (via .env) or generate new one."""
        try:
            key_env = getattr(settings, 'EMAIL_ENCRYPTION_KEY', '')
        except Exception:
            key_env = ''
        if key_env:
            logger.info(f"[EmailEncryption] Using EMAIL_ENCRYPTION_KEY from settings (len={len(key_env)})")
            return key_env.encode()
        
        # Generate new key (in production, store this securely)
        key = Fernet.generate_key()
        logger.warning(f"Generated new encryption key. Store this in EMAIL_ENCRYPTION_KEY: {key.decode()}")
        return key
    
    def encrypt_email(self, email: str) -> str:
        """Encrypt email address."""
        try:
            encrypted = self.cipher.encrypt(email.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt email: {e}")
            return email  # Return original if encryption fails
    
    def decrypt_email(self, encrypted_email: str) -> str:
        """Decrypt email address."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_email.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt email: {e}")
            return encrypted_email  # Return original if decryption fails


class MailjetEmailService:
    """Mailjet email service (v3.1) with error handling and fallback."""

    def __init__(self):
        self.api_key = getattr(settings, 'MAILJET_API_KEY', '')
        self.api_secret = getattr(settings, 'MAILJET_API_SECRET', '')
        self.from_email = getattr(settings, 'MAILJET_FROM_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@jacaranda.local'))
        self.from_name = getattr(settings, 'MAILJET_FROM_NAME', 'Jacaranda Talk')
        self.enabled = bool(self.api_key and self.api_secret)
        self.base_url = 'https://api.mailjet.com/v3.1/send'

    def send_otp_email(self, to_email: str, otp_code: str, user_id: int) -> Dict[str, Any]:
        """Send OTP email using Mailjet with fallback."""
        result = {
            'success': False,
            'method': 'unknown',
            'error': None,
            'retry_count': 0
        }
        if self.enabled:
            result = self._send_with_mailjet(to_email, otp_code, user_id)
            if result['success']:
                return result
        logger.info(f"Mailjet failed, using fallback for user {user_id}")
        return self._send_with_fallback(to_email, otp_code, user_id)

    def _send_with_mailjet(self, to_email: str, otp_code: str, user_id: int) -> Dict[str, Any]:
        """Send email using Mailjet API."""
        try:
            subject = 'Your Jacaranda Talk OTP'
            html_content = self._get_otp_email_template(otp_code)
            text_content = f"Your OTP code is: {otp_code}. It expires in 5 minutes."

            payload = {
                'Messages': [
                    {
                        'From': { 'Email': self.from_email, 'Name': self.from_name },
                        'To': [ { 'Email': to_email } ],
                        'Subject': subject,
                        'TextPart': text_content,
                        'HTMLPart': html_content,
                    }
                ]
            }

            response = requests.post(
                self.base_url,
                auth=(self.api_key, self.api_secret),
                json=payload,
                timeout=30
            )
            if response.status_code in (200, 202):
                logger.info(f"OTP email sent via Mailjet to {to_email} for user {user_id}")
                return { 'success': True, 'method': 'mailjet', 'status_code': response.status_code }
            error_msg = f"Mailjet API error: {response.status_code}"
            logger.error(f"Mailjet email failed for user {user_id}: {error_msg}")
            return { 'success': False, 'method': 'mailjet', 'status_code': response.status_code, 'error': error_msg }
        except requests.exceptions.RequestException as e:
            logger.error(f"Mailjet request failed for user {user_id}: {str(e)}")
            return { 'success': False, 'method': 'mailjet', 'error': f"Network error: {str(e)}", 'retry_count': 0 }
        except Exception as e:
            logger.error(f"Mailjet email failed for user {user_id}: {str(e)}")
            return { 'success': False, 'method': 'mailjet', 'error': str(e), 'retry_count': 0 }

    def _send_with_fallback(self, to_email: str, otp_code: str, user_id: int) -> Dict[str, Any]:
        """Send email using Django's fallback email backend."""
        try:
            send_mail(
                subject='Your Jacaranda Talk OTP',
                message=f'Your OTP code is: {otp_code}. It expires in 5 minutes.',
                from_email=self.from_email,
                recipient_list=[to_email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent via fallback to {to_email} for user {user_id}")
            return {'success': True, 'method': 'fallback', 'error': None}
        except Exception as e:
            logger.error(f"Fallback email failed for user {user_id}: {str(e)}")
            return {'success': False, 'method': 'fallback', 'error': str(e)}

    def _get_otp_email_template(self, otp_code: str) -> str:
        """Generate HTML email template for OTP."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Jacaranda Talk OTP</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .otp-code {{ background-color: #007bff; color: white; font-size: 24px; font-weight: bold; padding: 15px 30px; border-radius: 8px; text-align: center; margin: 20px 0; letter-spacing: 3px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Jacaranda Talk</h1>
                <p>Your One-Time Password</p>
            </div>
            <div class="content">
                <h2>Hello!</h2>
                <p>You requested a one-time password to access your Jacaranda Talk account.</p>
                <div class="otp-code">{otp_code}</div>
                <div class="warning">
                    <strong>⚠️ Important:</strong>
                    <ul>
                        <li>This code expires in 5 minutes</li>
                        <li>Never share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                </div>
                <p>Enter this code in the login form to complete your authentication.</p>
            </div>
            <div class="footer"><p>This is an automated message from Jacaranda Talk</p></div>
        </body>
        </html>
        """


class EmailServiceManager:
    """Main email service manager with caching and retry logic."""
    
    def __init__(self):
        self.mailjet_service = MailjetEmailService()
        self.encryption = EmailEncryption()
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def send_otp_with_retry(self, to_email: str, otp_code: str, user_id: int) -> Dict[str, Any]:
        """
        Send OTP email with retry logic and caching.
        """
        # Rate limiting - use EMAIL_RATE_LIMIT_SECONDS from settings, default to 10 seconds
        rate_limit_seconds = getattr(settings, 'EMAIL_RATE_LIMIT_SECONDS', 10)
        rate_limit_key = f"email:rate_limit:{user_id}"
        if cache.get(rate_limit_key):
            return {
                'success': False,
                'error': f'OTP requests are limited to once every {rate_limit_seconds} seconds. Please wait before requesting another OTP.',
                'method': 'rate_limit'
            }
        cache.set(rate_limit_key, True, timeout=rate_limit_seconds)
        
        # Try sending with retries
        for attempt in range(self.max_retries):
            result = self.mailjet_service.send_otp_email(to_email, otp_code, user_id)
            
            if result['success']:
                self._log_email_send(user_id, to_email, result['method'], success=True)
                return result
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        self._log_email_send(user_id, to_email, result.get('method', 'unknown'), success=False)
        return result
    
    def _log_email_send(self, user_id: int, email: str, method: str, success: bool):
        """Log email sending attempts for monitoring."""
        log_data = {
            'user_id': user_id,
            'email': email[:3] + '***@' + email.split('@')[1] if '@' in email else '***',
            'method': method,
            'success': success,
            'timestamp': time.time()
        }
        
        if success:
            logger.info(f"Email sent successfully: {log_data}")
        else:
            logger.error(f"Email send failed: {log_data}")
    
    def encrypt_user_email(self, email: str) -> str:
        """Encrypt user email for storage."""
        return self.encryption.encrypt_email(email)
    
    def decrypt_user_email(self, encrypted_email: str) -> str:
        """Decrypt user email for use."""
        return self.encryption.decrypt_email(encrypted_email)


# Global email service instance
email_service = EmailServiceManager()
