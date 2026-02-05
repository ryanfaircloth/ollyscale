/**
 * Timestamp conversion utilities for OTLP API
 */

/**
 * Convert RFC3339 timestamp string to nanoseconds since Unix epoch
 * @param rfc3339 - RFC3339 formatted timestamp string
 * @returns Nanoseconds since Unix epoch
 */
export function rfc3339ToNanoseconds(rfc3339: string): number {
  const date = new Date(rfc3339);
  const milliseconds = date.getTime();
  return milliseconds * 1_000_000; // Convert milliseconds to nanoseconds
}

/**
 * Convert nanoseconds since Unix epoch to RFC3339 timestamp string
 * @param nanoseconds - Nanoseconds since Unix epoch
 * @returns RFC3339 formatted timestamp string
 */
export function nanosecondsToRfc3339(nanoseconds: number): string {
  const milliseconds = Math.floor(nanoseconds / 1_000_000);
  return new Date(milliseconds).toISOString();
}

/**
 * Get current time in nanoseconds
 * @returns Current time in nanoseconds since Unix epoch
 */
export function nowInNanoseconds(): number {
  return Date.now() * 1_000_000;
}
