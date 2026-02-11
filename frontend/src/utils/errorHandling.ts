import { AxiosError } from 'axios';

/**
 * Custom application error class
 */
export class AppError extends Error {
  public statusCode?: number;
  public details?: any;

  constructor(message: string, statusCode?: number, details?: any) {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.details = details;
    
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (typeof (Error as any).captureStackTrace === 'function') {
      (Error as any).captureStackTrace(this, AppError);
    }
  }
}

/**
 * Handle API errors and convert them to user-friendly messages
 */
export const handleApiError = (error: unknown): AppError => {
  // Handle Axios errors
  if (error instanceof AxiosError) {
    const statusCode = error.response?.status;
    const responseData = error.response?.data;

    // Handle specific status codes
    switch (statusCode) {
      case 400:
        return new AppError(
          responseData?.message || 'Invalid request. Please check your input.',
          400,
          responseData
        );

      case 401:
        return new AppError(
          'You are not authenticated. Please log in.',
          401,
          responseData
        );

      case 403:
        return new AppError(
          'You do not have permission to perform this action.',
          403,
          responseData
        );

      case 404:
        return new AppError(
          responseData?.message || 'The requested resource was not found.',
          404,
          responseData
        );

      case 422:
        // Validation errors
        const validationErrors = responseData?.detail || responseData?.errors;
        return new AppError(
          'Validation failed. Please check your input.',
          422,
          validationErrors
        );

      case 500:
        return new AppError(
          'An internal server error occurred. Please try again later.',
          500,
          responseData
        );

      case 503:
        return new AppError(
          'The service is temporarily unavailable. Please try again later.',
          503,
          responseData
        );

      default:
        return new AppError(
          responseData?.message || error.message || 'An unexpected error occurred.',
          statusCode,
          responseData
        );
    }
  }

  // Handle AppError instances
  if (error instanceof AppError) {
    return error;
  }

  // Handle generic Error instances
  if (error instanceof Error) {
    return new AppError(error.message);
  }

  // Handle unknown error types
  return new AppError('An unexpected error occurred.');
};

/**
 * Extract validation error messages from API response
 */
export const extractValidationErrors = (error: AppError): Record<string, string> => {
  if (error.statusCode !== 422 || !error.details) {
    return {};
  }

  const errors: Record<string, string> = {};

  // Handle FastAPI validation error format
  if (Array.isArray(error.details)) {
    error.details.forEach((detail: any) => {
      const field = detail.loc?.join('.') || 'unknown';
      errors[field] = detail.msg || 'Validation error';
    });
  }

  // Handle custom error format
  if (typeof error.details === 'object' && !Array.isArray(error.details)) {
    Object.entries(error.details).forEach(([key, value]) => {
      errors[key] = String(value);
    });
  }

  return errors;
};

/**
 * Format error message for display to user
 */
export const formatErrorMessage = (error: unknown): string => {
  const appError = handleApiError(error);
  return appError.message;
};
