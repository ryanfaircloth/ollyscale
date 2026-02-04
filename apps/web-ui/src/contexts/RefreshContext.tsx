import { createContext, useContext, useState, type ReactNode } from 'react';

interface RefreshContextType {
  enabled: boolean;
  interval: number;
  setEnabled: (enabled: boolean) => void;
  setInterval: (interval: number) => void;
  toggle: () => void;
}

const RefreshContext = createContext<RefreshContextType | undefined>(undefined);

export function RefreshProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabledState] = useState(() => {
    const stored = localStorage.getItem('ollyscale-auto-refresh-enabled');
    return stored !== 'false';
  });

  const [interval, setIntervalState] = useState(() => {
    const stored = localStorage.getItem('ollyscale-auto-refresh-interval');
    return stored ? parseInt(stored, 10) : 5000;
  });

  const setEnabled = (value: boolean) => {
    setEnabledState(value);
    localStorage.setItem('ollyscale-auto-refresh-enabled', String(value));
  };

  const setInterval = (value: number) => {
    setIntervalState(value);
    localStorage.setItem('ollyscale-auto-refresh-interval', String(value));
  };

  const toggle = () => {
    setEnabled(!enabled);
  };

  return (
    <RefreshContext.Provider value={{ enabled, interval, setEnabled, setInterval, toggle }}>
      {children}
    </RefreshContext.Provider>
  );
}

export function useRefresh() {
  const context = useContext(RefreshContext);
  if (!context) {
    throw new Error('useRefresh must be used within RefreshProvider');
  }
  return context;
}
