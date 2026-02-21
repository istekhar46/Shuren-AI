/**
 * Input Validation Utilities
 * 
 * Provides validation functions for API request data.
 * These functions validate input before sending to the backend.
 */

/**
 * Validate email format
 * @param email - Email address to validate
 * @returns True if email is valid
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 * @param password - Password to validate
 * @returns True if password meets minimum requirements
 */
export function isValidPassword(password: string): boolean {
  // Minimum 8 characters
  return password.length >= 8;
}

/**
 * Validate required string field
 * @param value - String value to validate
 * @returns True if string is not empty
 */
export function isNonEmptyString(value: string): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Validate positive number
 * @param value - Number to validate
 * @returns True if number is positive
 */
export function isPositiveNumber(value: number): boolean {
  return typeof value === 'number' && value > 0 && !isNaN(value);
}

/**
 * Validate non-negative number
 * @param value - Number to validate
 * @returns True if number is non-negative
 */
export function isNonNegativeNumber(value: number): boolean {
  return typeof value === 'number' && value >= 0 && !isNaN(value);
}

/**
 * Validate number within range
 * @param value - Number to validate
 * @param min - Minimum value (inclusive)
 * @param max - Maximum value (inclusive)
 * @returns True if number is within range
 */
export function isNumberInRange(value: number, min: number, max: number): boolean {
  return typeof value === 'number' && value >= min && value <= max && !isNaN(value);
}

/**
 * Validate UUID format
 * @param uuid - UUID string to validate
 * @returns True if string is a valid UUID
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

/**
 * Validate ISO date string
 * @param dateString - Date string to validate
 * @returns True if string is a valid ISO date
 */
export function isValidISODate(dateString: string): boolean {
  const date = new Date(dateString);
  return !isNaN(date.getTime()) && dateString === date.toISOString();
}

/**
 * Validate time string (HH:MM format)
 * @param timeString - Time string to validate
 * @returns True if string is valid time format
 */
export function isValidTimeString(timeString: string): boolean {
  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;
  return timeRegex.test(timeString);
}

/**
 * Validate array is not empty
 * @param array - Array to validate
 * @returns True if array has at least one element
 */
export function isNonEmptyArray<T>(array: T[]): boolean {
  return Array.isArray(array) && array.length > 0;
}

/**
 * Validate object has required keys
 * @param obj - Object to validate
 * @param requiredKeys - Array of required key names
 * @returns True if object has all required keys
 */
export function hasRequiredKeys(obj: Record<string, any>, requiredKeys: string[]): boolean {
  return requiredKeys.every(key => key in obj);
}
