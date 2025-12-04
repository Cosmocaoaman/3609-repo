import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginForm() {
  const { login, register, mfaPending } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isBanned, setIsBanned] = useState(false);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [isLoading, setIsLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsBanned(false);
    setIsLoading(true);
    
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, password, username, isAdmin);
        alert('Registration successful, please login');
        setMode('login');
        setUsername(''); // Clear username after successful registration
        setIsAdmin(false); // Clear admin checkbox after successful registration
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Action failed';
      setError(errorMessage);
      
      // Check if this is a banned user error
      if (errorMessage.includes('banned') || errorMessage.includes('contact the administrator')) {
        setIsBanned(true);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="login-form">
      <div className="login-input-group">
        <input 
          type="email"
          className="login-input"
          placeholder="Enter email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input 
          type="password"
          className="login-input"
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {mode === 'register' && (
          <>
            <input 
              type="text"
              className="login-input"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              maxLength={50}
              required
            />
            <div className="form-check" style={{ marginTop: '10px', marginBottom: '10px' }}>
              <input 
                className="form-check-input"
                type="checkbox"
                id="isAdminCheck"
                checked={isAdmin}
                onChange={(e) => setIsAdmin(e.target.checked)}
              />
              <label className="form-check-label" htmlFor="isAdminCheck">
                Register as admin
              </label>
            </div>
          </>
        )}
      </div>
      
      {error && (
        <div className={`login-error ${isBanned ? 'login-error-warning' : ''}`}>
          {isBanned && <div className="login-error-title"><i className="bi bi-ban"></i> Account Banned</div>}
          {error}
        </div>
      )}
      
      <button 
        type="submit" 
        className="btn btn-primary btn-lg login-submit"
        disabled={mfaPending || isLoading}
      >
        {isLoading ? (
          <>
            <div className="loading"></div>
            {mode === 'login' ? 'Sending...' : 'Registering...'}
          </>
        ) : (
          mode === 'login' ? 'Send Verification Code' : 'Create Account'
        )}
      </button>
      
      <div className="login-footer">
        <button 
          type="button" 
          className="login-switch"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? 'Don\'t have an account? Register' : 'Already have an account? Login'}
        </button>
      </div>
    </form>
  );
}


