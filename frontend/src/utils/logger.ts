/**
 * API Logger Utilities
 * 
 * Provides structured logging for API requests, responses, and errors
 * with configurable log levels and output formatting.
 */

import type { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Log levels in order of severity
 */
export const LogLevel = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  NONE: 4,
} as const;

export type LogLevel = typeof LogLevel[keyof typeof LogLevel];

/**
 * Log entry structure
 */
interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
  context?: string;
}

/**
 * Logger configuration options
 */
interface LoggerConfig {
  /**
   * Minimum log level to output (default: INFO in production, DEBUG in development)
   */
  minLevel?: LogLevel;

  /**
   * Enable console output (default: true)
   */
  enableConsole?: boolean;

  /**
   * Enable storing logs in memory (default: false)
   */
  enableStorage?: boolean;

  /**
   * Maximum number of logs to store in memory (default: 100)
   */
  maxStoredLogs?: number;

  /**
   * Context prefix for all logs (e.g., 'API', 'Service')
   */
  context?: string;
}

/**
 * APILogger class for structured API logging
 * 
 * Features:
 * - Configurable log levels
 * - Request/response logging
 * - Error tracking
 * - In-memory log storage
 * - Performance metrics
 */
export class APILogger {
  private config: Required<LoggerConfig>;
  private logs: LogEntry[] = [];

  /**
   * Create a new APILogger instance
   * @param config - Logger configuration options
   */
  constructor(config: LoggerConfig = {}) {
    const isDevelopment = import.meta.env.DEV;

    this.config = {
      minLevel: config.minLevel ?? (isDevelopment ? LogLevel.DEBUG : LogLevel.INFO),
      enableConsole: config.enableConsole ?? true,
      enableStorage: config.enableStorage ?? false,
      maxStoredLogs: config.maxStoredLogs ?? 100,
      context: config.context ?? 'API',
    };
  }

  /**
   * Create a log entry
   * @param level - Log level
   * @param message - Log message
   * @param data - Additional data to log
   * @param context - Optional context override
   */
  private createLogEntry(
    level: LogLevel,
    message: string,
    data?: any,
    context?: string
  ): LogEntry {
    return {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
      context: context ?? this.config.context,
    };
  }

  /**
   * Output log entry to console
   * @param entry - Log entry to output
   */
  private outputToConsole(entry: LogEntry): void {
    if (!this.config.enableConsole) {
      return;
    }

    const prefix = `[${entry.timestamp}] [${entry.context}]`;
    const message = `${prefix} ${entry.message}`;

    switch (entry.level) {
      case LogLevel.DEBUG:
        console.debug(message, entry.data ?? '');
        break;
      case LogLevel.INFO:
        console.info(message, entry.data ?? '');
        break;
      case LogLevel.WARN:
        console.warn(message, entry.data ?? '');
        break;
      case LogLevel.ERROR:
        console.error(message, entry.data ?? '');
        break;
    }
  }

  /**
   * Store log entry in memory
   * @param entry - Log entry to store
   */
  private storeLog(entry: LogEntry): void {
    if (!this.config.enableStorage) {
      return;
    }

    this.logs.push(entry);

    // Trim logs if exceeding max size
    if (this.logs.length > this.config.maxStoredLogs) {
      this.logs.shift();
    }
  }

  /**
   * Log a message at specified level
   * @param level - Log level
   * @param message - Log message
   * @param data - Additional data to log
   * @param context - Optional context override
   */
  private log(level: LogLevel, message: string, data?: any, context?: string): void {
    // Check if log level meets minimum threshold
    if (level < this.config.minLevel) {
      return;
    }

    const entry = this.createLogEntry(level, message, data, context);
    this.outputToConsole(entry);
    this.storeLog(entry);
  }

  /**
   * Log debug message
   * @param message - Log message
   * @param data - Additional data to log
   */
  debug(message: string, data?: any): void {
    this.log(LogLevel.DEBUG, message, data);
  }

  /**
   * Log info message
   * @param message - Log message
   * @param data - Additional data to log
   */
  info(message: string, data?: any): void {
    this.log(LogLevel.INFO, message, data);
  }

  /**
   * Log warning message
   * @param message - Log message
   * @param data - Additional data to log
   */
  warn(message: string, data?: any): void {
    this.log(LogLevel.WARN, message, data);
  }

  /**
   * Log error message
   * @param message - Log message
   * @param data - Additional data to log
   */
  error(message: string, data?: any): void {
    this.log(LogLevel.ERROR, message, data);
  }

  /**
   * Log API request
   * @param config - Axios request configuration
   */
  logRequest(config: AxiosRequestConfig): void {
    const { method, url, params, data } = config;

    this.debug(`Request: ${method?.toUpperCase()} ${url}`, {
      params,
      data,
      headers: config.headers,
    });
  }

  /**
   * Log API response
   * @param response - Axios response
   * @param duration - Request duration in milliseconds
   */
  logResponse(response: AxiosResponse, duration?: number): void {
    const { status, config, data } = response;
    const { method, url } = config;

    const durationText = duration ? ` (${duration}ms)` : '';
    this.info(`Response: ${method?.toUpperCase()} ${url} - ${status}${durationText}`, {
      status,
      data,
      headers: response.headers,
    });
  }

  /**
   * Log API error
   * @param error - Axios error
   * @param duration - Request duration in milliseconds
   */
  logError(error: AxiosError, duration?: number): void {
    const { config, response, message } = error;
    const method = config?.method?.toUpperCase();
    const url = config?.url;

    const durationText = duration ? ` (${duration}ms)` : '';

    if (response) {
      // Server responded with error status
      this.error(
        `Error: ${method} ${url} - ${response.status}${durationText}`,
        {
          status: response.status,
          statusText: response.statusText,
          data: response.data,
          message,
        }
      );
    } else if (config) {
      // Request was made but no response received
      this.error(`Error: ${method} ${url} - No response${durationText}`, {
        message,
        code: error.code,
      });
    } else {
      // Error setting up request
      this.error(`Error: Request setup failed`, {
        message,
      });
    }
  }

  /**
   * Get all stored logs
   * @returns Array of log entries
   */
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Get logs filtered by level
   * @param level - Minimum log level to include
   * @returns Filtered array of log entries
   */
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level >= level);
  }

  /**
   * Clear all stored logs
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * Get logger statistics
   * @returns Object with log counts by level
   */
  getStats(): Record<string, number> {
    const stats = {
      total: this.logs.length,
      debug: 0,
      info: 0,
      warn: 0,
      error: 0,
    };

    for (const log of this.logs) {
      switch (log.level) {
        case LogLevel.DEBUG:
          stats.debug++;
          break;
        case LogLevel.INFO:
          stats.info++;
          break;
        case LogLevel.WARN:
          stats.warn++;
          break;
        case LogLevel.ERROR:
          stats.error++;
          break;
      }
    }

    return stats;
  }

  /**
   * Update logger configuration
   * @param config - Partial configuration to update
   */
  updateConfig(config: Partial<LoggerConfig>): void {
    this.config = {
      ...this.config,
      ...config,
    };
  }

  /**
   * Create a child logger with additional context
   * @param context - Context string to append
   * @returns New logger instance with combined context
   */
  createChild(context: string): APILogger {
    return new APILogger({
      ...this.config,
      context: `${this.config.context}:${context}`,
    });
  }
}

/**
 * Default logger instance
 * Can be used across the application for API logging
 */
export const apiLogger = new APILogger({
  enableStorage: import.meta.env.DEV, // Store logs in development only
});

/**
 * Create a performance timer for measuring request duration
 * @returns Object with start time and elapsed function
 */
export function createTimer(): { start: number; elapsed: () => number } {
  const start = performance.now();

  return {
    start,
    elapsed: () => Math.round(performance.now() - start),
  };
}

/**
 * Sanitize sensitive data from logs
 * @param data - Data object to sanitize
 * @param sensitiveKeys - Array of keys to redact (default: common sensitive fields)
 * @returns Sanitized data object
 */
export function sanitizeLogData(
  data: any,
  sensitiveKeys: string[] = ['password', 'token', 'authorization', 'api_key', 'secret']
): any {
  if (!data || typeof data !== 'object') {
    return data;
  }

  const sanitized = Array.isArray(data) ? [...data] : { ...data };

  for (const key in sanitized) {
    const lowerKey = key.toLowerCase();

    // Check if key is sensitive
    if (sensitiveKeys.some(sensitiveKey => lowerKey.includes(sensitiveKey))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof sanitized[key] === 'object' && sanitized[key] !== null) {
      // Recursively sanitize nested objects
      sanitized[key] = sanitizeLogData(sanitized[key], sensitiveKeys);
    }
  }

  return sanitized;
}
