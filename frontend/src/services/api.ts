import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { apiLogger } from '../utils/logger';
import { retryRequest, RetryPresets } from '../utils/retry';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
  },
});

// Request interceptor: Add JWT token, security headers, and logging
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Start performance timer
    (config as any).metadata = { startTime: performance.now() };

    // Add JWT token
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add security headers
    config.headers['X-Content-Type-Options'] = 'nosniff';
    config.headers['X-Frame-Options'] = 'DENY';
    config.headers['X-XSS-Protection'] = '1; mode=block';

    // Log request
    apiLogger.logRequest(config);

    return config;
  },
  (error) => {
    apiLogger.logError(error);
    return Promise.reject(error);
  }
);

// Response interceptor: Handle errors, logging, and retry logic
api.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const duration = (response.config as any).metadata?.startTime
      ? Math.round(performance.now() - (response.config as any).metadata.startTime)
      : undefined;

    // Log response
    apiLogger.logResponse(response, duration);

    return response;
  },
  async (error: AxiosError) => {
    // Calculate request duration
    const duration = (error.config as any)?.metadata?.startTime
      ? Math.round(performance.now() - (error.config as any).metadata.startTime)
      : undefined;

    // Log error
    apiLogger.logError(error, duration);

    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Check if request should be retried
    const shouldRetry = 
      error.config && 
      !error.config.headers?.['X-No-Retry'] &&
      (error.response?.status === 408 ||
       error.response?.status === 429 ||
       error.response?.status === 503 ||
       error.response?.status === 504 ||
       !error.response); // Network errors

    if (shouldRetry) {
      try {
        // Retry the request with exponential backoff
        const result = await retryRequest(
          () => axios.request(error.config!),
          {
            ...RetryPresets.standard,
            onRetry: (_err, attempt, delay) => {
              apiLogger.warn(
                `Retrying request (attempt ${attempt}/${RetryPresets.standard.maxRetries}) after ${delay}ms`,
                {
                  method: error.config?.method,
                  url: error.config?.url,
                  status: error.response?.status,
                }
              );
            },
          }
        );
        return result;
      } catch (retryError) {
        // All retries failed, return original error
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
