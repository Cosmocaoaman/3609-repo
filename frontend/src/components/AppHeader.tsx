import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AnonymousToggle } from './AnonymousToggle';

function AppHeader() {
  const { loggedIn, isAnonymous, logout } = useAuth() as any;

  return (
    <header className="app-header">
      <div className="centered-container header-content">
        {/* Left: brand */}
        <Link to="/" className="logo">Jacaranda Talk</Link>
        {/* Right: toggle + links */}
        <div className="nav-actions">
          {loggedIn ? (
            <>
              <AnonymousToggle />
              <NavLink to="/me" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                Profile
              </NavLink>
              <NavLink to="/profile/settings" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Settings</NavLink>
              <NavLink to="/threads" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Threads</NavLink>
              <NavLink to="/threads/new" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>New Thread</NavLink>
              <button className="nav-link" onClick={() => logout()}>Logout</button>
            </>
          ) : (
            <NavLink to="/login" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>Sign in</NavLink>
          )}
        </div>
      </div>
    </header>
  );
}

export default AppHeader;


