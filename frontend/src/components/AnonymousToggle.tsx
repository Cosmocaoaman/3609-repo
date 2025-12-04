import React from 'react';
import { useAuth } from '../context/AuthContext';

interface AnonymousToggleProps {
  className?: string;
}

export function AnonymousToggle({ className = '' }: AnonymousToggleProps) {
  const { isAnonymous, toggleAnonymous, isAdmin, isStaff, isSuperuser } = useAuth() as any;
  const [isLoading, setIsLoading] = React.useState(false);

  const handleToggle = async () => {
    if (isLoading) return;
    if (isAdmin || isStaff || isSuperuser) return; // admins cannot toggle
    setIsLoading(true);
    try {
      await toggleAnonymous(!isAnonymous);
    } catch (error) {
      console.error('Failed to toggle anonymous mode:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const isAdminUser = isAdmin || isStaff || isSuperuser;

  return (
    <button
      type="button"
      className={`nav-link ${className}`}
      onClick={handleToggle}
      disabled={isLoading || isAdminUser}
      aria-pressed={isAnonymous}
      title={isAdminUser ? 'Admin Mode' : (isAnonymous ? 'Switch to normal mode' : 'Switch to anonymous mode')}
      style={{ cursor: isAdminUser ? 'not-allowed' : 'pointer' }}
    >
      <span style={{ marginRight: '8px' }}>{isAnonymous ? <i className="bi bi-moon"></i> : <i className="bi bi-sun"></i>}</span>
      {isAnonymous ? 'Anonymous' : 'Normal'}
      {isLoading && <span className="loading-spinner ms-2"></span>}
    </button>
  );
}
