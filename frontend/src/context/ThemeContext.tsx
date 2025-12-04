import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

type ThemeMode = 'light' | 'dark';

type ThemeContextValue = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = 'app-theme-mode';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = typeof window !== 'undefined' ? (window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null) : null;
    return saved ?? 'light';
  });

  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      root.classList.toggle('theme-dark', mode === 'dark');
    }
    try { window.localStorage.setItem(STORAGE_KEY, mode); } catch {}
  }, [mode]);

  const value = useMemo<ThemeContextValue>(() => ({
    mode,
    setMode: (m) => setModeState(m),
    toggle: () => setModeState(prev => (prev === 'dark' ? 'light' : 'dark')),
  }), [mode]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}


