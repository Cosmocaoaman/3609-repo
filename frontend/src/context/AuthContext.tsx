import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import { useTheme } from './ThemeContext';
import { login as apiLogin, verifyOtp as apiVerify, logout as apiLogout, register as apiRegister, toggleAnonymousMode } from '../api/auth';

type AuthState = {
  userId?: number;
  username?: string;
  isStaff?: boolean;
  isSuperuser?: boolean;
  isAdmin?: boolean;
  loggedIn: boolean;
  mfaPending: boolean;
  pendingUserId?: number;
  isAnonymous: boolean;
  isInitialized?: boolean;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<void>;
  verifyOtp: (otp: string) => Promise<void>;
  register: (email: string, password: string, confirm: string, username: string, isAdmin?: boolean) => Promise<void>;
  logout: () => Promise<void>;
  toggleAnonymous: (isAnonymous: boolean) => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ loggedIn: false, mfaPending: false, isAnonymous: false, isInitialized: false });
  const theme = (() => {
    try { return useTheme(); } catch { return undefined; }
  })();

  // Restore session on mount (best-effort)
  useEffect(() => {
    (async () => {
      // Optimistic restore from localStorage to avoid flicker while validating
      try {
        const res = await fetch('/api/auth/whoami/', { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          if (data?.logged_in) {
            setState(prev => ({
              ...prev,
              loggedIn: true,
              username: data.username,
              userId: data.user_id,
              isAnonymous: !!data.is_anonymous,
              isStaff: data.is_staff,
              isSuperuser: data.is_superuser,
              isAdmin: data.is_admin,
              mfaPending: false,
              isInitialized: true,
            }));
            // Admin users always use light mode regardless of anonymous state
            const isAdminUser = data.is_admin || data.is_staff || data.is_superuser;
            theme?.setMode(isAdminUser ? 'light' : (data.is_anonymous ? 'dark' : 'light'));
            return;
          }
        }
      } catch {}
      // Not logged in -> force light
      theme?.setMode('light');
      setState(prev => ({ ...prev, isInitialized: true }));
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    ...state,
    async login(email, password) {
      const res = await apiLogin(email, password);
      if (res.mfa_required) {
        setState({ loggedIn: false, mfaPending: true, pendingUserId: res.user_id, isAnonymous: false, isInitialized: true });
        theme?.setMode('light');
      }
    },
    async verifyOtp(otp) {
      if (!state.pendingUserId) throw new Error('No pending user');
      const res = await apiVerify(state.pendingUserId, otp);
      setState({
        loggedIn: true,
        mfaPending: false,
        userId: res.user_id,
        username: res.username,
        isAnonymous: false,
        isStaff: (res as any)?.is_staff,
        isSuperuser: (res as any)?.is_superuser,
        isAdmin: (res as any)?.is_admin,
        isInitialized: true,
      });
      // Admin users always use light mode
      const isAdminUser = (res as any)?.is_admin || (res as any)?.is_staff || (res as any)?.is_superuser;
      theme?.setMode(isAdminUser ? 'light' : 'light');
    },
    async register(email, password, confirm, username, isAdmin = false) {
      await apiRegister(email, password, confirm, username, isAdmin);
    },
    async logout() {
      await apiLogout();
      setState({ loggedIn: false, mfaPending: false, isAnonymous: false, isInitialized: true });
      theme?.setMode('light');
    },
    async toggleAnonymous(isAnonymous) {
      await toggleAnonymousMode(isAnonymous);
      setState(prev => ({ ...prev, isAnonymous }));
      // Admin users should always stay in light mode
      const isAdminUser = state.isAdmin || state.isStaff || state.isSuperuser;
      theme?.setMode(isAdminUser ? 'light' : (isAnonymous ? 'dark' : 'light'));
    },
    async refreshUser() {
      try {
        const res = await fetch('/api/auth/whoami/', { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          if (data?.logged_in) {
            setState(prev => ({
              ...prev,
              loggedIn: true,
              username: data.username,
              userId: data.user_id,
              isAnonymous: !!data.is_anonymous,
              isStaff: data.is_staff,
              isSuperuser: data.is_superuser,
              isAdmin: data.is_admin,
              mfaPending: false,
              isInitialized: true,
            }));
            // Admin users always use light mode
            const isAdminUser = data.is_admin || data.is_staff || data.is_superuser;
            theme?.setMode(isAdminUser ? 'light' : (data.is_anonymous ? 'dark' : 'light'));
          }
        }
      } catch {}
    }
  }), [state]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


