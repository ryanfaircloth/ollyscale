import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for persisting state to localStorage with type safety
 * Automatically syncs across tabs/windows when storage changes
 *
 * @param key - localStorage key
 * @param initialValue - Initial value if key doesn't exist
 * @returns [storedValue, setValue] - Similar to useState
 *
 * @example
 * ```tsx
 * const [theme, setTheme] = useLocalStorage<'light' | 'dark'>('theme', 'light');
 * const [filters, setFilters] = useLocalStorage<Filter[]>('filters', []);
 * ```
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void] {
  // Initialize state with value from localStorage or initialValue
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Update localStorage when value changes
  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        // Allow value to be a function (like useState)
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));

        // Dispatch custom event to sync across tabs
        window.dispatchEvent(
          new CustomEvent('localStorage', {
            detail: { key, value: valueToStore },
          })
        );
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // Listen for changes from other tabs/windows
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent | CustomEvent) => {
      if (e instanceof StorageEvent) {
        // Native storage event (from other tabs)
        if (e.key === key && e.newValue) {
          try {
            setStoredValue(JSON.parse(e.newValue) as T);
          } catch (error) {
            console.warn(`Error parsing localStorage change for key "${key}":`, error);
          }
        }
      } else {
        // Custom event (from same tab via setValue)
        const detail = (e as CustomEvent).detail;
        if (detail.key === key) {
          setStoredValue(detail.value as T);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange as EventListener);
    window.addEventListener('localStorage', handleStorageChange as EventListener);

    return () => {
      window.removeEventListener('storage', handleStorageChange as EventListener);
      window.removeEventListener('localStorage', handleStorageChange as EventListener);
    };
  }, [key]);

  return [storedValue, setValue];
}
