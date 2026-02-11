/**
 * Retry Utilities
 * 
 * Provides retry logic for failed API requests with exponential backoff
 * and configurable retry strategies.
 */

import axios, { AxiosError } from 'axios';

/**
 * Retry configuration options
 */
export interface RetryOptions {
  /**
   * Maximum number of retry attempts (default: 3)
   */
  maxRetries?: number;

  /**
   * Initial delay in milliseconds before first retry (default: 1000ms)
   */
  initialDelay?: number;

  /**
   * Maximum delay in milliseconds between retries (default: 10000ms)
   */
  maxDelay?: number;

  /**
   * Backoff multiplier for exponential backoff (default: 2)
   */
  backoffMultiplier?: number;

  /**
   * HTTP status codes that should trigger a retry (default: [408, 429, 500, 502, 503, 504])
   */
  retryableStatusCodes?: number[];

  /**
   * Custom function to determine if error should be retried
   */
  shouldRetry?: (error: Error, attempt: number) => boolean;

  /**
   * Callback function called before each retry attempt
   */
  onRetry?: (error: Error, attempt: number, delay: number) => void;
}

/**
 * Default retryable HTTP status codes
 * - 408: Request Timeout
 * - 429: Too Many Requests
 * - 500: Internal Server Error
 * - 502: Bad Gateway
 * - 503: Service Unavailable
 * - 504: Gateway Timeout
 */
const DEFAULT_RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

/**
 * Check if an error is retryable based on status code
 * @param error - Error to check
 * @param retryableStatusCodes - List of status codes that should trigger retry
 * @returns True if error should be retried
 */
function isRetryableError(error: Error, retryableStatusCodes: number[]): boolean {
  // Check if it's an Axios error with a response
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;

    // Network errors (no response) are retryable
    if (!axiosError.response) {
      return true;
    }

    // Check if status code is in retryable list
    const statusCode = axiosError.response.status;
    return retryableStatusCodes.includes(statusCode);
  }

  // Network errors and timeouts are retryable
  if (error.name === 'NetworkError' || error.name === 'TimeoutError') {
    return true;
  }

  return false;
}

/**
 * Calculate delay for next retry attempt using exponential backoff
 * @param attempt - Current attempt number (0-indexed)
 * @param initialDelay - Initial delay in milliseconds
 * @param backoffMultiplier - Multiplier for exponential backoff
 * @param maxDelay - Maximum delay in milliseconds
 * @returns Delay in milliseconds
 */
function calculateDelay(
  attempt: number,
  initialDelay: number,
  backoffMultiplier: number,
  maxDelay: number
): number {
  const delay = initialDelay * Math.pow(backoffMultiplier, attempt);
  return Math.min(delay, maxDelay);
}

/**
 * Sleep for specified milliseconds
 * @param ms - Milliseconds to sleep
 * @returns Promise that resolves after delay
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a request function with exponential backoff
 * 
 * @param requestFn - Async function that performs the request
 * @param options - Retry configuration options
 * @returns Promise that resolves with the request result
 * @throws Error if all retry attempts fail
 * 
 * @example
 * ```typescript
 * const data = await retryRequest(
 *   () => api.get('/users'),
 *   { maxRetries: 3, initialDelay: 1000 }
 * );
 * ```
 */
export async function retryRequest<T>(
  requestFn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffMultiplier = 2,
    retryableStatusCodes = DEFAULT_RETRYABLE_STATUS_CODES,
    shouldRetry,
    onRetry,
  } = options;

  let lastError: Error;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Attempt the request
      const result = await requestFn();
      return result;
    } catch (error) {
      lastError = error as Error;

      // Check if we've exhausted all retries
      if (attempt === maxRetries) {
        throw lastError;
      }

      // Determine if error should be retried
      const shouldRetryError = shouldRetry
        ? shouldRetry(lastError, attempt)
        : isRetryableError(lastError, retryableStatusCodes);

      if (!shouldRetryError) {
        throw lastError;
      }

      // Calculate delay for next attempt
      const delay = calculateDelay(attempt, initialDelay, backoffMultiplier, maxDelay);

      // Call onRetry callback if provided
      if (onRetry) {
        onRetry(lastError, attempt + 1, delay);
      }

      // Wait before next retry
      await sleep(delay);
    }
  }

  // This should never be reached, but TypeScript requires it
  throw lastError!;
}

/**
 * Create a retry wrapper for a specific request function
 * 
 * @param requestFn - Async function that performs the request
 * @param options - Retry configuration options
 * @returns Wrapped function that includes retry logic
 * 
 * @example
 * ```typescript
 * const getUserWithRetry = withRetry(
 *   (userId: string) => api.get(`/users/${userId}`),
 *   { maxRetries: 3 }
 * );
 * 
 * const user = await getUserWithRetry('123');
 * ```
 */
export function withRetry<TArgs extends any[], TResult>(
  requestFn: (...args: TArgs) => Promise<TResult>,
  options: RetryOptions = {}
): (...args: TArgs) => Promise<TResult> {
  return async (...args: TArgs): Promise<TResult> => {
    return retryRequest(() => requestFn(...args), options);
  };
}

/**
 * Retry configuration presets for common scenarios
 */
export const RetryPresets = {
  /**
   * Quick retry for fast operations (3 retries, 500ms initial delay)
   */
  quick: {
    maxRetries: 3,
    initialDelay: 500,
    maxDelay: 5000,
    backoffMultiplier: 2,
  } as RetryOptions,

  /**
   * Standard retry for normal operations (3 retries, 1s initial delay)
   */
  standard: {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
  } as RetryOptions,

  /**
   * Aggressive retry for critical operations (5 retries, 2s initial delay)
   */
  aggressive: {
    maxRetries: 5,
    initialDelay: 2000,
    maxDelay: 30000,
    backoffMultiplier: 2,
  } as RetryOptions,

  /**
   * Conservative retry for non-critical operations (2 retries, 2s initial delay)
   */
  conservative: {
    maxRetries: 2,
    initialDelay: 2000,
    maxDelay: 10000,
    backoffMultiplier: 2,
  } as RetryOptions,
};
