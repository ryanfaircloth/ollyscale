import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce } from './useDebounce';

describe('useDebounce', () => {
  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('test', 500));
    expect(result.current).toBe('test');
  });

  it('should debounce value changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    expect(result.current).toBe('initial');

    // Update value
    rerender({ value: 'updated', delay: 500 });

    // Should still show initial value immediately
    expect(result.current).toBe('initial');

    // After delay, should show updated value
    await waitFor(
      () => {
        expect(result.current).toBe('updated');
      },
      { timeout: 1000 }
    );
  });

  it('should cancel previous debounce on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: 'first' },
      }
    );

    // Rapid changes
    rerender({ value: 'second' });
    rerender({ value: 'third' });
    rerender({ value: 'final' });

    // Should only see the final value after delay
    await waitFor(
      () => {
        expect(result.current).toBe('final');
      },
      { timeout: 400 }
    );
  });

  it('should cleanup timeout on unmount', () => {
    vi.useFakeTimers();
    const { unmount } = renderHook(() => useDebounce('test', 500));

    unmount();

    // Advance timers to ensure no errors
    vi.runAllTimers();
    vi.useRealTimers();
  });
});
