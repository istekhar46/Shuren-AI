import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

// Mock scrollIntoView (not available in JSDOM)
Element.prototype.scrollIntoView = () => {};

// Cleanup after each test
afterEach(() => {
  cleanup();
});
