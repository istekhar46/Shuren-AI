import type {
  OnboardingWorkoutPlan,
  OnboardingMealPlan,
} from '../types/onboarding.types';

/**
 * Plan Detection Service
 * 
 * Detects and parses workout and meal plans from agent responses.
 * Note: This is a fallback mechanism. Ideally, the backend should send
 * structured plan data in a separate field rather than embedded in text.
 */
export const planDetectionService = {
  /**
   * Detect if message contains a workout plan
   * @param message - Agent response message
   * @returns Parsed workout plan or null if not detected
   */
  detectWorkoutPlan(message: string): OnboardingWorkoutPlan | null {
    // Look for workout plan indicators
    const hasWorkoutIndicators = /workout plan|training plan|exercise schedule|workout program/i.test(message);
    
    if (!hasWorkoutIndicators) {
      return null;
    }
    
    // For now, return null and rely on structured responses from backend
    // In the future, we can implement text parsing if needed
    console.info('Workout plan detected in message. Waiting for structured data from backend.');
    return null;
  },

  /**
   * Detect if message contains a meal plan
   * @param message - Agent response message
   * @returns Parsed meal plan or null if not detected
   */
  detectMealPlan(message: string): OnboardingMealPlan | null {
    // Look for meal plan indicators
    const hasMealIndicators = /meal plan|nutrition plan|diet plan|calorie target|macro breakdown/i.test(message);
    
    if (!hasMealIndicators) {
      return null;
    }
    
    // For now, return null and rely on structured responses from backend
    // In the future, we can implement text parsing if needed
    console.info('Meal plan detected in message. Waiting for structured data from backend.');
    return null;
  },

  /**
   * Parse workout plan from text
   * Note: This is a fallback. Ideally backend sends structured JSON.
   * @param text - Message text containing workout plan
   * @returns Parsed workout plan
   * @throws Error if parsing is not implemented
   */
  parseWorkoutPlan(_text: string): OnboardingWorkoutPlan {
    // Implementation depends on backend response format
    // For now, throw error and rely on structured responses
    throw new Error('Plan parsing not implemented - backend should send structured data');
  },

  /**
   * Parse meal plan from text
   * Note: This is a fallback. Ideally backend sends structured JSON.
   * @param text - Message text containing meal plan
   * @returns Parsed meal plan
   * @throws Error if parsing is not implemented
   */
  parseMealPlan(_text: string): OnboardingMealPlan {
    // Implementation depends on backend response format
    // For now, throw error and rely on structured responses
    throw new Error('Plan parsing not implemented - backend should send structured data');
  },
};
