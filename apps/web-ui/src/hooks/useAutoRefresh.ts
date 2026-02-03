import { useEffect, useRef } from 'react';
import { useRefresh } from '@/contexts/RefreshContext';

/**
 * Auto-refresh hook that refetches data at a configured interval
 * Respects the global auto-refresh settings from RefreshContext
 */
export function useAutoRefresh(refetchFn: () => void) {
  const { enabled, interval } = useRefresh();
  const refetchFnRef = useRef(refetchFn);

  // Keep refetchFn reference up to date
  useEffect(() => {
    refetchFnRef.current = refetchFn;
  }, [refetchFn]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const intervalId = setInterval(() => {
      refetchFnRef.current();
    }, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [enabled, interval]);
}
