import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { resendOtp } from '../api/auth';

export default function OtpForm() {
  const { mfaPending, verifyOtp, pendingUserId } = useAuth();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  
  if (!mfaPending || !pendingUserId) return null;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setIsLoading(true);
    
    try {
      await verifyOtp(otp);
    } catch (err: any) {
      setError(err.message || 'Invalid code, please try again');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleResend() {
    setError(null);
    setSuccessMessage(null);
    setIsResending(true);
    
    try {
      // Call resend API without email - backend will get it from user record
      const result = await resendOtp(pendingUserId);
      setSuccessMessage(result.message || 'OTP code has been resent to your email');
      // Clear OTP input
      setOtp('');
    } catch (err: any) {
      setError(err.message || 'Failed to resend OTP. Please try again.');
    } finally {
      setIsResending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="otp-form">
      <div className="otp-input-group">
        <input 
          type="text"
          className="otp-input"
          placeholder="Enter 6-digit code"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
          maxLength={6}
          autoComplete="one-time-code"
          required
        />
        <div className="otp-hint">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
          </svg>
          <span>Code sent to your email</span>
        </div>
      </div>
      
      {error && (
        <div className="otp-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="currentColor"/>
          </svg>
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="otp-success" style={{ 
          background: '#d4edda', 
          color: '#155724', 
          padding: '12px', 
          borderRadius: '8px', 
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
          </svg>
          {successMessage}
        </div>
      )}
      
      <button 
        type="submit" 
        className="btn btn-primary btn-lg otp-submit"
        disabled={otp.length !== 6 || isLoading}
      >
        {isLoading ? (
          <>
            <div className="loading"></div>
            Verifying...
          </>
        ) : (
          'Verify & Login'
        )}
      </button>
      
      <div className="otp-footer">
        <p className="otp-timer">Code expires in 5 minutes</p>
        <button 
          type="button" 
          className="otp-resend"
          onClick={handleResend}
          disabled={isResending || isLoading}
        >
          {isResending ? 'Sending...' : 'Resend code'}
        </button>
      </div>
    </form>
  );
}


