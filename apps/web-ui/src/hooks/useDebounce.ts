import { useEffect, useState } from 'react';

/**
 * Debounce hook that delays updating a value until after a specified delay
 * Useful for search inputs to reduce API calls while typing
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 500ms)
 * @returns Debounced value
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, 500);
 *
 * useEffect(() => {
 *   if (debouncedSearch) {
 *     // API call with debounced value
 *     searchAPI(debouncedSearch);
 *   }
 * }, [debouncedSearch]);
 * ```
 */
export function useDebounce<T>(value: T, delay = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up the timeout
    const timeoutId = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timeout if value changes before delay completes
    return () => clearTimeout(timeoutId);
  }, [value, delay]);

  return debouncedValue;
}
