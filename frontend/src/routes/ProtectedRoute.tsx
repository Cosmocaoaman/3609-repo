import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute
 * Guards child routes based on authentication state.
 * - If MFA is pending, redirect to /otp so users can finish verification.
 * - If not logged in, redirect to /login.
 * - Otherwise, render the nested route via <Outlet />.
 */
const ProtectedRoute: React.FC = () => {
  const { loggedIn, mfaPending, isInitialized } = useAuth() as any;

  if (!isInitialized) return <Outlet />;
  if (mfaPending) {
    return <Navigate to="/otp" replace />;
  }
  if (!loggedIn) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
};

export default ProtectedRoute;



