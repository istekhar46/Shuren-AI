// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
  };
}

// User Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  oauth_provider: string | null;
  is_active: boolean;
  created_at: string;
}

// Agent Types
export type AgentType =
  | 'workout_planning'
  | 'diet_planning'
  | 'supplement_guidance'
  | 'tracking_adjustment'
  | 'scheduling_reminder'
  | 'general_assistant';

// Onboarding Types
export interface OnboardingStepData {
  step: number;
  data: Record<string, any>;
}

export interface OnboardingResponse {
  success: boolean;
  message: string;
  nextStep?: number;
}

// Profile Types
export interface Goal {
  type: 'fat_loss' | 'muscle_gain' | 'general_fitness';
  targetWeight?: number;
  targetDate?: string;
}

export interface PhysicalConstraint {
  type: 'equipment' | 'injury' | 'limitation';
  description: string;
}

export interface DietaryPreference {
  dietType: 'omnivore' | 'vegetarian' | 'vegan' | 'pescatarian';
  allergies: string[];
  dislikes: string[];
}

export interface MealPlan {
  dailyCalories: number;
  macros: {
    protein: number;
    carbs: number;
    fats: number;
  };
  mealsPerDay: number;
}

export interface MealSchedule {
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  time: string; // HH:MM format
}

export interface WorkoutSchedule {
  daysPerWeek: number;
  preferredDays: string[]; // ['monday', 'wednesday', 'friday']
  preferredTime: string; // HH:MM format
  sessionDuration: number; // minutes
}

export interface HydrationPreference {
  dailyGoal: number; // liters
  reminderInterval: number; // minutes
}

export interface LifestyleBaseline {
  energyLevel: 'low' | 'medium' | 'high';
  stressLevel: 'low' | 'medium' | 'high';
  sleepQuality: 'poor' | 'fair' | 'good' | 'excellent';
}

export interface NotificationPreference {
  workoutReminders: boolean;
  mealReminders: boolean;
  hydrationReminders: boolean;
  motivationalMessages: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  fitnessLevel: 'beginner' | 'intermediate' | 'advanced';
  goals: Goal[];
  physicalConstraints: PhysicalConstraint[];
  dietaryPreferences: DietaryPreference;
  mealPlan: MealPlan;
  mealSchedule: MealSchedule[];
  workoutSchedule: WorkoutSchedule;
  hydrationPreferences: HydrationPreference;
  lifestyleBaseline: LifestyleBaseline;
  notificationPreferences: NotificationPreference;
  isLocked: boolean;
  createdAt: string;
  updatedAt: string;
}

// Chat Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentType: AgentType;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  agentType: AgentType;
  conversationId?: string;
}

export interface ChatResponse {
  message: string;
  agentType: AgentType;
  conversationId: string;
  timestamp: string;
}

// Voice Session Types
export interface VoiceSessionRequest {
  agentType: AgentType;
}

export interface VoiceSessionResponse {
  roomName: string;
  token: string;
  url: string;
  agentType: AgentType;
}

export interface VoiceSessionStatus {
  roomName: string;
  connected: boolean;
  participantCount: number;
  duration: number;
  agentConnected: boolean;
}

export interface TranscriptionMessage {
  id: string;
  speaker: 'user' | 'agent';
  text: string;
  timestamp: Date;
  isFinal: boolean;
}

export interface SessionStatus {
  connected: boolean;
  participantCount: number;
  duration: number;
}

// Meal Types
export interface Ingredient {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: string;
}

export interface Dish {
  id: string;
  name: string;
  description: string;
  ingredients: Ingredient[];
  instructions: string[];
  macros: {
    calories: number;
    protein: number;
    carbs: number;
    fats: number;
  };
  prepTime: number; // minutes
  cookTime: number; // minutes
}

export interface Meal {
  id: string;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  dish: Dish;
  scheduledTime: string;
  date: string;
}

export interface ShoppingListItem {
  ingredient: Ingredient;
  totalQuantity: number;
  meals: string[]; // meal IDs
}

export interface ShoppingList {
  items: ShoppingListItem[];
  generatedAt: string;
}

// Workout Types
export interface ExerciseSet {
  setNumber: number;
  targetReps: number;
  targetWeight?: number;
  actualReps?: number;
  actualWeight?: number;
  completed: boolean;
}

export interface Exercise {
  id: string;
  name: string;
  muscleGroup: string;
  sets: ExerciseSet[];
  instructions: string[];
  gifUrl?: string;
}

export interface WorkoutSession {
  id: string;
  date: string;
  exercises: Exercise[];
  completed: boolean;
  duration?: number;
}

export interface WorkoutLog {
  sessionId: string;
  exerciseId: string;
  setNumber: number;
  reps: number;
  weight?: number;
}
