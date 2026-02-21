/**
 * API Cache Utilities
 * 
 * Provides in-memory caching for API responses to reduce redundant requests
 * and improve application performance.
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

/**
 * APICache class for managing cached API responses
 * 
 * Features:
 * - Time-based expiration (TTL)
 * - Manual cache invalidation
 * - Memory-efficient storage
 * - Type-safe cache entries
 */
export class APICache {
  private cache: Map<string, CacheEntry<any>>;
  private defaultTTL: number;

  /**
   * Create a new APICache instance
   * @param defaultTTL - Default time-to-live in milliseconds (default: 5 minutes)
   */
  constructor(defaultTTL: number = 5 * 60 * 1000) {
    this.cache = new Map();
    this.defaultTTL = defaultTTL;
  }

  /**
   * Get cached data by key
   * @param key - Cache key
   * @returns Cached data if valid, undefined if expired or not found
   */
  get<T>(key: string): T | undefined {
    const entry = this.cache.get(key);

    if (!entry) {
      return undefined;
    }

    // Check if entry has expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return undefined;
    }

    return entry.data as T;
  }

  /**
   * Set cached data with key
   * @param key - Cache key
   * @param data - Data to cache
   * @param ttl - Time-to-live in milliseconds (optional, uses default if not provided)
   */
  set<T>(key: string, data: T, ttl?: number): void {
    const timeToLive = ttl ?? this.defaultTTL;
    const timestamp = Date.now();

    const entry: CacheEntry<T> = {
      data,
      timestamp,
      expiresAt: timestamp + timeToLive,
    };

    this.cache.set(key, entry);
  }

  /**
   * Check if a key exists and is valid in cache
   * @param key - Cache key
   * @returns True if key exists and hasn't expired
   */
  has(key: string): boolean {
    const entry = this.cache.get(key);

    if (!entry) {
      return false;
    }

    // Check if entry has expired
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * Delete a specific cache entry
   * @param key - Cache key to delete
   * @returns True if entry was deleted, false if not found
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Clear expired cache entries
   * @returns Number of entries cleared
   */
  clearExpired(): number {
    const now = Date.now();
    let clearedCount = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
        clearedCount++;
      }
    }

    return clearedCount;
  }

  /**
   * Get cache statistics
   * @returns Object with cache size and expired entries count
   */
  getStats(): { size: number; expired: number } {
    const now = Date.now();
    let expiredCount = 0;

    for (const entry of this.cache.values()) {
      if (now > entry.expiresAt) {
        expiredCount++;
      }
    }

    return {
      size: this.cache.size,
      expired: expiredCount,
    };
  }

  /**
   * Get or set cached data with a factory function
   * If data exists in cache and is valid, return it.
   * Otherwise, call the factory function, cache the result, and return it.
   * 
   * @param key - Cache key
   * @param factory - Async function to generate data if not cached
   * @param ttl - Time-to-live in milliseconds (optional)
   * @returns Cached or newly generated data
   */
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    // Check if data exists in cache
    const cached = this.get<T>(key);
    if (cached !== undefined) {
      return cached;
    }

    // Generate new data
    const data = await factory();

    // Cache the result
    this.set(key, data, ttl);

    return data;
  }

  /**
   * Invalidate cache entries matching a pattern
   * @param pattern - String pattern or RegExp to match keys
   * @returns Number of entries invalidated
   */
  invalidatePattern(pattern: string | RegExp): number {
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
    let invalidatedCount = 0;

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
        invalidatedCount++;
      }
    }

    return invalidatedCount;
  }
}

/**
 * Default cache instance with 5-minute TTL
 * Can be used across the application for API response caching
 */
export const apiCache = new APICache();

/**
 * Generate a cache key from URL and parameters
 * @param url - API endpoint URL
 * @param params - Query parameters or request body
 * @returns Cache key string
 */
export function generateCacheKey(url: string, params?: Record<string, any>): string {
  if (!params || Object.keys(params).length === 0) {
    return url;
  }

  const sortedParams = Object.keys(params)
    .sort()
    .map(key => `${key}=${JSON.stringify(params[key])}`)
    .join('&');

  return `${url}?${sortedParams}`;
}
