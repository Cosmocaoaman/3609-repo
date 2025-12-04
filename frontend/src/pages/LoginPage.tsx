import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm';
import { useAuth } from '../context/AuthContext';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { mfaPending, loggedIn } = useAuth();

  useEffect(() => {
    if (mfaPending) {
      navigate('/otp', { replace: true });
    } else if (loggedIn) {
      navigate('/', { replace: true });
    }
  }, [mfaPending, loggedIn, navigate]);

  return (
    <div className="page-container">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 7.5V9C15 10.1 14.1 11 13 11H11C9.9 11 9 10.1 9 9V7.5L3 7V9C3 10.1 3.9 11 5 11V20C5 21.1 5.9 22 7 22H9C10.1 22 11 21.1 11 20V16H13V20C13 21.1 13.9 22 15 22H17C18.1 22 19 21.1 19 20V11C20.1 11 21 10.1 21 9Z" fill="currentColor"/>
              </svg>
            </div>
            <h2 className="login-title">Login to Jacaranda Talk</h2>
            <p className="login-subtitle">Enter your email address to get started</p>
          </div>
          <LoginForm />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

