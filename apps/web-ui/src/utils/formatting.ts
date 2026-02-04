import { formatDistanceToNow, format, parseISO } from 'date-fns';

/**
 * Format RFC3339 timestamp to relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(timestamp: string): string {
  try {
    const date = parseISO(timestamp);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return timestamp;
  }
}

/**
 * Format RFC3339 timestamp to human-readable format with timezone
 */
export function formatTimestamp(timestamp: string, formatStr = 'MMM d, yyyy HH:mm:ss.SSS'): string {
  try {
    const date = parseISO(timestamp);
    const formatted = format(date, formatStr);
    // Append timezone abbreviation
    const tzAbbr = format(date, 'zzz');
    return `${formatted} ${tzAbbr}`;
  } catch {
    return timestamp;
  }
}

/**
 * Format duration in seconds to human-readable format
 */
export function formatDuration(durationSeconds: number): string {
  if (durationSeconds < 0.001) {
    return `${(durationSeconds * 1_000_000).toFixed(0)}μs`;
  }
  if (durationSeconds < 1) {
    return `${(durationSeconds * 1000).toFixed(2)}ms`;
  }
  if (durationSeconds < 60) {
    return `${durationSeconds.toFixed(2)}s`;
  }
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = (durationSeconds % 60).toFixed(2);
  return `${minutes}m ${seconds}s`;
}

/**
 * Format trace/span ID to short format (first 8 chars)
 */
export function formatTraceId(id: string, short = true): string {
  return short && id.length > 8 ? id.substring(0, 8) : id;
}

/**
 * Format byte size to human-readable format
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format attribute value for display - handles objects, arrays, and primitives
 */
export function formatAttributeValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  // Handle primitives
  if (typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  // Handle objects and arrays - stringify with formatting
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return '[Complex Object]';
    }
  }

  return String(value);
}
