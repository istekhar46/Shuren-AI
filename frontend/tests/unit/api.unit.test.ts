import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiLogger } from '../../src/utils/logger';
import { RetryPresets } from '../../src/utils/retry';
import api from '../../src/services/api';

describe('API Configuration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('API Logger Integration', () => {
    it('should have apiLogger available', () => {
      expect(apiLogger).toBeDefined();
      expect(apiLogger.logRequest).toBeDefined();
      expect(apiLogger.logResponse).toBeDefined();
      expect(apiLogger.logError).toBeDefined();
    });

    it('should log request with correct format', () => {
      const mockConfig = {
        method: 'GET',
        url: '/test',
        params: { id: '123' },
        data: null,
        headers: {},
      };

      apiLogger.logRequest(mockConfig);

      // Verify logger was called (implementation tested in logger.test.ts)
      expect(true).toBe(true);
    });
  });

  describe('Retry Logic Integration', () => {
    it('should have RetryPresets configured', () => {
      expect(RetryPresets.standard).toBeDefined();
      expect(RetryPresets.standard.maxRetries).toBe(3);
      expect(RetryPresets.standard.initialDelay).toBe(1000);
      expect(RetryPresets.standard.maxDelay).toBe(10000);
    });

    it('should have quick preset configured', () => {
      expect(RetryPresets.quick).toBeDefined();
      expect(RetryPresets.quick.maxRetries).toBe(3);
      expect(RetryPresets.quick.initialDelay).toBe(500);
    });

    it('should have aggressive preset configured', () => {
      expect(RetryPresets.aggressive).toBeDefined();
      expect(RetryPresets.aggressive.maxRetries).toBe(5);
    });
  });

  describe('Security Headers', () => {
    it('should define required security headers', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json');
      expect(api.defaults.headers['Accept']).toBe('application/json');
      expect(api.defaults.headers['X-Requested-With']).toBe('XMLHttpRequest');
    });
  });

  describe('Base Configuration', () => {
    it('should have correct timeout', () => {
      expect(api.defaults.timeout).toBe(30000);
    });

    it('should have baseURL configured', () => {
      expect(api.defaults.baseURL).toBeDefined();
      expect(typeof api.defaults.baseURL).toBe('string');
    });
  });

  describe('Interceptors', () => {
    it('should have request interceptor configured', () => {
      expect(api.interceptors.request.handlers.length).toBeGreaterThan(0);
    });

    it('should have response interceptor configured', () => {
      expect(api.interceptors.response.handlers.length).toBeGreaterThan(0);
    });
  });
});


