# Minimal Frontend for Backend Testing - Design Document

## 1. Overview

This document describes the technical design for a React-based web frontend that serves as a testing interface for the Shuren AI backend. The frontend enables comprehensive testing of authentication, onboarding, AI agent interactions (text and voice), meal management, and workout tracking.

**Design Goals:**
- Validate all Phase 1 & 2 backend endpoints
- Test AI agent orchestration and responses
- Validate LiveKit voice integration
- Provide clear visibility into backend behavior
- Maintain clean, maintainable code for future expansion

**Technology Stack:**
- React with TypeScript (latest)
- Vite for build tooling
- React Router for navigation
- Context API for state management
- Axios for HTTP requests
- Shadcn/ui for UI components (Tailwind CSS)
- LiveKit React SDK for voice sessions

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Pages      │  │  Components  │  │   Contexts   │  │
│  │              │  │              │  │              │  │
│  │ - Login      │  │ - Auth       │  │ - Auth       │  │
│  │ - Dashboard  │  │ - Onboarding │  │ - User       │  │
│  │ - Chat       │  │ - Chat       │  │ - Voice      │  │
│  │ - Voice      │  │ - Meals      │  │              │  │
│  │ - Meals      │  │ - Workouts   │  │              │  │
│  │ - Workouts   │  │              │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┴─────────────────┘           │
│                           │                             │
│                  ┌────────▼────────┐                    │
│                  │   Services      │                    │
│                  │                 │                    │
│                  │ - API Client    │                    │
│                  │ - Auth Service  │                    │
│                  │ - Chat Service  │                    │
│                  │ - Voice Service │                    │
│                  └────────┬────────┘                    │
└───────────────────────────┼─────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌─────────▼────────┐
│  FastAPI       │                    │   LiveKit        │
│  Backend       │                    │   Server         │
│                │                    │                  │
│ - REST API     │                    │ - Voice Rooms   │
│ - AI Agents    │                    │ - STT/TTS       │
│ - Database     │                    │ - WebRTC        │
└────────────────┘                    └──────────────────┘
```

### 2.2 Component Hierarchy


```
App
├── AuthProvider (Context)
│   ├── LoginPage
│   └── RegisterPage
│
├── UserProvider (Context)
│   ├── OnboardingPage
│   │   ├── OnboardingStep1 (Fitness Level)
│   │   ├── OnboardingStep2 (Goals)
│   │   ├── OnboardingStep3 (Physical Constraints)
│   │   ├── OnboardingStep4 (Dietary Preferences)
│   │   ├── OnboardingStep5 (Meal Plan)
│   │   ├── OnboardingStep6 (Meal Schedule)
│   │   ├── OnboardingStep7 (Workout Schedule)
│   │   ├── OnboardingStep8 (Hydration)
│   │   ├── OnboardingStep9 (Lifestyle Baseline)
│   │   ├── OnboardingStep10 (Notifications)
│   │   ├── OnboardingStep11 (Review)
│   │   └── OnboardingStep12 (Confirmation)
│   │
│   ├── DashboardPage
│   │   ├── ProfileSummary
│   │   ├── MealPlanSummary
│   │   ├── WorkoutScheduleSummary
│   │   └── QuickActions
│   │
│   ├── ChatPage
│   │   ├── AgentSelector
│   │   ├── MessageList
│   │   ├── MessageInput
│   │   └── LoadingIndicator
│   │
│   ├── VoiceProvider (Context)
│   │   └── VoicePage
│   │       ├── AgentSelector
│   │       ├── VoiceControls
│   │       ├── TranscriptionDisplay
│   │       ├── SessionStatus
│   │       └── LatencyIndicator
│   │
│   ├── MealsPage
│   │   ├── MealPlanView
│   │   ├── MealDetails
│   │   ├── DishBrowser
│   │   └── ShoppingList
│   │
│   └── WorkoutsPage
│       ├── WorkoutSchedule
│       ├── TodayWorkout
│       ├── ExerciseLogger
│       └── WorkoutHistory
```

## 3. State Management

### 3.1 Context Architecture

The application uses React Context API for state management with three primary contexts:

**AuthContext:**
- Manages authentication state (token, user identity)
- Provides login, logout, register functions
- Handles token persistence in localStorage
- Redirects to login on 401 errors

**UserContext:**
- Manages user profile data
- Provides profile refresh function
- Caches profile data to minimize API calls
- Handles profile lock/unlock state

**VoiceContext:**
- Manages LiveKit room connection state
- Provides voice session start/stop functions
- Tracks transcription and agent responses
- Handles microphone permissions

### 3.2 State Flow Diagrams

#### Authentication Flow
```
[User] → [Login Form] → [AuthService.login()]
                              ↓
                    [POST /auth/login]
                              ↓
                    [Store JWT in localStorage]
                              ↓
                    [Update AuthContext]
                              ↓
                    [Redirect to Dashboard]
```

#### Onboarding Flow
```
[User] → [Step 1 Form] → [OnboardingService.saveStep(1, data)]
                              ↓
                    [POST /onboarding/step]
                              ↓
                    [Backend validates & saves]
                              ↓
                    [Navigate to Step 2]
                              ↓
                         [Repeat for steps 2-11]
                              ↓
                    [Step 12: Lock Profile]
                              ↓
                    [POST /onboarding/step (step 12)]
                              ↓
                    [Backend locks profile]
                              ↓
                    [Redirect to Dashboard]
```

#### Text Chat Flow
```
[User] → [Type Message] → [ChatService.sendMessage(text, agentType)]
                              ↓
                    [POST /chat/chat]
                              ↓
                    [Backend routes to agent]
                              ↓
                    [Agent processes with LangChain]
                              ↓
                    [Response returned]
                              ↓
                    [Display in MessageList]
```

#### Voice Session Flow
```
[User] → [Start Voice] → [VoiceService.startSession(agentType)]
                              ↓
                    [POST /voice-sessions/start]
                              ↓
                    [Backend creates LiveKit room]
                              ↓
                    [Returns room token]
                              ↓
                    [Connect to LiveKit room]
                              ↓
                    [Request microphone access]
                              ↓
                    [Publish audio track]
                              ↓
                    [Agent joins room]
                              ↓
                    [Deepgram STT transcribes]
                              ↓
                    [Agent processes with LLM]
                              ↓
                    [Cartesia TTS generates audio]
                              ↓
                    [Audio plays through speakers]
                              ↓
                    [User clicks End Session]
                              ↓
                    [DELETE /voice-sessions/{room}]
                              ↓
                    [Disconnect from room]
```

## 4. Components and Interfaces

### 4.1 Core Components

#### AuthProvider
```typescript
interface AuthContextType {
  isAuthenticated: boolean;
  user: { id: string; email: string } | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}
```

#### UserProvider
```typescript
interface UserContextType {
  profile: UserProfile | null;
  refreshProfile: () => Promise<void>;
  unlockProfile: () => Promise<void>;
  loading: boolean;
}

interface UserProfile {
  id: string;
  email: string;
  fitnessLevel: string;
  goals: Goal[];
  mealPlan: MealPlanSummary;
  workoutSchedule: WorkoutScheduleSummary;
  isLocked: boolean;
}
```

#### VoiceProvider
```typescript
interface VoiceContextType {
  isConnected: boolean;
  roomName: string | null;
  agentType: string | null;
  transcription: TranscriptionMessage[];
  startSession: (agentType: string) => Promise<void>;
  endSession: () => Promise<void>;
  sessionStatus: SessionStatus;
  latency: number;
  error: string | null;
}

interface TranscriptionMessage {
  id: string;
  speaker: 'user' | 'agent';
  text: string;
  timestamp: Date;
  isFinal: boolean;
}

interface SessionStatus {
  connected: boolean;
  participantCount: number;
  duration: number;
}
```

### 4.2 Page Components

#### LoginPage
- Email and password inputs
- Submit button with loading state
- Link to registration
- Error message display

#### OnboardingPage
- Progress indicator (1-12)
- Dynamic step component rendering
- Back/Next navigation
- Form validation
- Error handling

#### DashboardPage
- Profile summary card
- Meal plan summary
- Workout schedule summary
- Quick action buttons (Chat, Voice, Meals, Workouts)

#### ChatPage
- Agent type selector dropdown
- Message list with auto-scroll
- Message input with send button
- Loading indicator during agent response
- Error message display

#### VoicePage
- Agent type selector
- Start/Stop session button
- Voice activity indicator
- Real-time transcription display
- Session status (connected, participant count, duration)
- Latency indicator
- Error message display

#### MealsPage
- Meal plan view (weekly grid)
- Meal details modal
- Dish browser with search
- Shopping list generator
- Substitution request button (opens chat)

#### WorkoutsPage
- Workout schedule calendar
- Today's workout detail view
- Exercise logger (sets, reps, weight)
- Mark complete button
- Workout history list

### 4.3 Shared Components

#### ProtectedRoute
```typescript
interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOnboarding?: boolean;
}
```
- Checks authentication
- Redirects to login if not authenticated
- Optionally checks onboarding completion

#### LoadingSpinner
- Centered spinner with optional message
- Used during async operations

#### ErrorMessage
```typescript
interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
}
```
- Displays error with dismiss button
- Auto-dismiss after 5 seconds

#### ConfirmDialog
```typescript
interface ConfirmDialogProps {
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
  cancelText?: string;
}
```
- Modal dialog for destructive actions
- Used for profile unlock, session end, etc.

## 5. Data Models

### 5.1 TypeScript Interfaces


```typescript
// Authentication
interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
  };
}

// Onboarding
interface OnboardingStepData {
  step: number;
  data: Record<string, any>;
}

interface OnboardingResponse {
  success: boolean;
  message: string;
  nextStep?: number;
}

// Profile
interface UserProfile {
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

interface Goal {
  type: 'fat_loss' | 'muscle_gain' | 'general_fitness';
  targetWeight?: number;
  targetDate?: string;
}

interface PhysicalConstraint {
  type: 'equipment' | 'injury' | 'limitation';
  description: string;
}

interface DietaryPreference {
  dietType: 'omnivore' | 'vegetarian' | 'vegan' | 'pescatarian';
  allergies: string[];
  dislikes: string[];
}

interface MealPlan {
  dailyCalories: number;
  macros: {
    protein: number;
    carbs: number;
    fats: number;
  };
  mealsPerDay: number;
}

interface MealSchedule {
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  time: string; // HH:MM format
}

interface WorkoutSchedule {
  daysPerWeek: number;
  preferredDays: string[]; // ['monday', 'wednesday', 'friday']
  preferredTime: string; // HH:MM format
  sessionDuration: number; // minutes
}

interface HydrationPreference {
  dailyGoal: number; // liters
  reminderInterval: number; // minutes
}

interface LifestyleBaseline {
  energyLevel: 'low' | 'medium' | 'high';
  stressLevel: 'low' | 'medium' | 'high';
  sleepQuality: 'poor' | 'fair' | 'good' | 'excellent';
}

interface NotificationPreference {
  workoutReminders: boolean;
  mealReminders: boolean;
  hydrationReminders: boolean;
  motivationalMessages: boolean;
}

// Chat
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentType: AgentType;
  timestamp: string;
}

type AgentType = 
  | 'workout_planning'
  | 'diet_planning'
  | 'supplement_guidance'
  | 'tracking_adjustment'
  | 'scheduling_reminder'
  | 'general_assistant';

interface ChatRequest {
  message: string;
  agentType: AgentType;
  conversationId?: string;
}

interface ChatResponse {
  message: string;
  agentType: AgentType;
  conversationId: string;
  timestamp: string;
}

// Voice Session
interface VoiceSessionRequest {
  agentType: AgentType;
}

interface VoiceSessionResponse {
  roomName: string;
  token: string;
  url: string;
  agentType: AgentType;
}

interface VoiceSessionStatus {
  roomName: string;
  connected: boolean;
  participantCount: number;
  duration: number;
  agentConnected: boolean;
}

// Meals
interface Meal {
  id: string;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  dish: Dish;
  scheduledTime: string;
  date: string;
}

interface Dish {
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

interface Ingredient {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: string;
}

interface ShoppingList {
  items: ShoppingListItem[];
  generatedAt: string;
}

interface ShoppingListItem {
  ingredient: Ingredient;
  totalQuantity: number;
  meals: string[]; // meal IDs
}

// Workouts
interface WorkoutSession {
  id: string;
  date: string;
  exercises: Exercise[];
  completed: boolean;
  duration?: number;
}

interface Exercise {
  id: string;
  name: string;
  muscleGroup: string;
  sets: ExerciseSet[];
  instructions: string[];
  gifUrl?: string;
}

interface ExerciseSet {
  setNumber: number;
  targetReps: number;
  targetWeight?: number;
  actualReps?: number;
  actualWeight?: number;
  completed: boolean;
}

interface WorkoutLog {
  sessionId: string;
  exerciseId: string;
  setNumber: number;
  reps: number;
  weight?: number;
}
```

## 6. Service Layer Design

### 6.1 API Client Configuration

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized: Clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 6.2 Service Implementations

#### AuthService
```typescript
// services/authService.ts
import api from './api';

export const authService = {
  async register(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/register', { email, password });
    return response.data;
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('auth_token');
  },

  getToken(): string | null {
    return localStorage.getItem('auth_token');
  },

  setToken(token: string): void {
    localStorage.setItem('auth_token', token);
  },
};
```

#### OnboardingService
```typescript
// services/onboardingService.ts
import api from './api';

export const onboardingService = {
  async saveStep(step: number, data: Record<string, any>): Promise<OnboardingResponse> {
    const response = await api.post('/onboarding/step', { step, data });
    return response.data;
  },

  async getProgress(): Promise<{ currentStep: number; completed: boolean }> {
    const response = await api.get('/onboarding/progress');
    return response.data;
  },
};
```

#### ChatService
```typescript
// services/chatService.ts
import api from './api';

export const chatService = {
  async sendMessage(message: string, agentType: AgentType): Promise<ChatResponse> {
    const response = await api.post('/chat/chat', { message, agent_type: agentType });
    return response.data;
  },

  async getHistory(conversationId?: string): Promise<ChatMessage[]> {
    const response = await api.get('/chat/history', {
      params: { conversation_id: conversationId },
    });
    return response.data;
  },

  // Streaming chat (SSE)
  streamMessage(
    message: string,
    agentType: AgentType,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): EventSource {
    const token = localStorage.getItem('auth_token');
    const url = new URL('/chat/stream', api.defaults.baseURL);
    url.searchParams.append('message', message);
    url.searchParams.append('agent_type', agentType);

    const eventSource = new EventSource(url.toString(), {
      headers: { Authorization: `Bearer ${token}` },
    } as any);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.done) {
        onComplete();
        eventSource.close();
      } else {
        onChunk(data.chunk);
      }
    };

    eventSource.onerror = (error) => {
      onError(new Error('Stream connection failed'));
      eventSource.close();
    };

    return eventSource;
  },
};
```

#### VoiceService
```typescript
// services/voiceService.ts
import api from './api';

export const voiceService = {
  async startSession(agentType: AgentType): Promise<VoiceSessionResponse> {
    const response = await api.post('/voice-sessions/start', { agent_type: agentType });
    return response.data;
  },

  async getStatus(roomName: string): Promise<VoiceSessionStatus> {
    const response = await api.get(`/voice-sessions/${roomName}/status`);
    return response.data;
  },

  async endSession(roomName: string): Promise<void> {
    await api.delete(`/voice-sessions/${roomName}`);
  },
};
```

#### ProfileService
```typescript
// services/profileService.ts
import api from './api';

export const profileService = {
  async getProfile(): Promise<UserProfile> {
    const response = await api.get('/profiles/me');
    return response.data;
  },

  async unlockProfile(): Promise<void> {
    await api.post('/profiles/me/unlock');
  },

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await api.put('/profiles/me', data);
    return response.data;
  },
};
```

#### MealService
```typescript
// services/mealService.ts
import api from './api';

export const mealService = {
  async getMealPlan(startDate?: string, endDate?: string): Promise<Meal[]> {
    const response = await api.get('/meals/plan', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  async getMealDetails(mealId: string): Promise<Meal> {
    const response = await api.get(`/meals/${mealId}`);
    return response.data;
  },

  async searchDishes(query: string): Promise<Dish[]> {
    const response = await api.get('/meals/dishes/search', { params: { q: query } });
    return response.data;
  },

  async generateShoppingList(startDate: string, endDate: string): Promise<ShoppingList> {
    const response = await api.post('/meals/shopping-list', { start_date: startDate, end_date: endDate });
    return response.data;
  },
};
```

#### WorkoutService
```typescript
// services/workoutService.ts
import api from './api';

export const workoutService = {
  async getSchedule(): Promise<WorkoutSession[]> {
    const response = await api.get('/workouts/schedule');
    return response.data;
  },

  async getTodayWorkout(): Promise<WorkoutSession | null> {
    const response = await api.get('/workouts/today');
    return response.data;
  },

  async logSet(log: WorkoutLog): Promise<void> {
    await api.post('/workouts/log', log);
  },

  async completeWorkout(sessionId: string): Promise<void> {
    await api.post(`/workouts/${sessionId}/complete`);
  },

  async getHistory(limit?: number): Promise<WorkoutSession[]> {
    const response = await api.get('/workouts/history', { params: { limit } });
    return response.data;
  },
};
```

## 7. LiveKit Integration

### 7.1 Voice Session Hook


```typescript
// hooks/useVoiceSession.ts
import { useState, useEffect, useCallback } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';
import { voiceService } from '../services/voiceService';

export const useVoiceSession = () => {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [transcription, setTranscription] = useState<TranscriptionMessage[]>([]);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>({
    connected: false,
    participantCount: 0,
    duration: 0,
  });
  const [latency, setLatency] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [roomName, setRoomName] = useState<string | null>(null);

  const startSession = useCallback(async (agentType: AgentType) => {
    try {
      setError(null);
      
      // Request microphone permission
      await navigator.mediaDevices.getUserMedia({ audio: true });

      // Get room token from backend
      const sessionData = await voiceService.startSession(agentType);
      
      // Create LiveKit room
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Set up event listeners
      newRoom.on(RoomEvent.Connected, () => {
        setIsConnected(true);
        setSessionStatus((prev) => ({ ...prev, connected: true }));
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setSessionStatus((prev) => ({ ...prev, connected: false }));
      });

      newRoom.on(RoomEvent.ParticipantConnected, () => {
        setSessionStatus((prev) => ({
          ...prev,
          participantCount: newRoom.participants.size + 1,
        }));
      });

      newRoom.on(RoomEvent.ParticipantDisconnected, () => {
        setSessionStatus((prev) => ({
          ...prev,
          participantCount: newRoom.participants.size + 1,
        }));
      });

      // Listen for transcription data (from agent)
      newRoom.on(RoomEvent.DataReceived, (payload, participant) => {
        const decoder = new TextDecoder();
        const data = JSON.parse(decoder.decode(payload));
        
        if (data.type === 'transcription') {
          setTranscription((prev) => [
            ...prev,
            {
              id: data.id,
              speaker: data.speaker,
              text: data.text,
              timestamp: new Date(data.timestamp),
              isFinal: data.isFinal,
            },
          ]);
        }

        if (data.type === 'latency') {
          setLatency(data.value);
        }
      });

      // Connect to room
      await newRoom.connect(sessionData.url, sessionData.token);
      
      setRoom(newRoom);
      setRoomName(sessionData.roomName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start voice session');
      throw err;
    }
  }, []);

  const endSession = useCallback(async () => {
    if (room && roomName) {
      try {
        await room.disconnect();
        await voiceService.endSession(roomName);
        setRoom(null);
        setRoomName(null);
        setIsConnected(false);
        setTranscription([]);
        setSessionStatus({ connected: false, participantCount: 0, duration: 0 });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to end session');
      }
    }
  }, [room, roomName]);

  // Track session duration
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      setSessionStatus((prev) => ({
        ...prev,
        duration: prev.duration + 1,
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, [isConnected]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
    };
  }, [room]);

  return {
    room,
    isConnected,
    transcription,
    sessionStatus,
    latency,
    error,
    roomName,
    startSession,
    endSession,
  };
};
```

### 7.2 Voice Page Component

```typescript
// pages/VoicePage.tsx
import { useState } from 'react';
import { useVoiceSession } from '../hooks/useVoiceSession';
import { AudioVisualizer } from '@livekit/components-react';

export const VoicePage = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('general_assistant');
  const {
    room,
    isConnected,
    transcription,
    sessionStatus,
    latency,
    error,
    startSession,
    endSession,
  } = useVoiceSession();

  const handleStart = async () => {
    try {
      await startSession(selectedAgent);
    } catch (err) {
      console.error('Failed to start session:', err);
    }
  };

  const handleEnd = async () => {
    await endSession();
  };

  return (
    <div className="voice-page">
      <h1>Voice Session</h1>

      {!isConnected ? (
        <div className="session-setup">
          <label>
            Select Agent:
            <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value as AgentType)}>
              <option value="workout_planning">Workout Planning</option>
              <option value="diet_planning">Diet Planning</option>
              <option value="supplement_guidance">Supplement Guidance</option>
              <option value="tracking_adjustment">Tracking & Adjustment</option>
              <option value="scheduling_reminder">Scheduling & Reminder</option>
              <option value="general_assistant">General Assistant</option>
            </select>
          </label>
          <button onClick={handleStart}>Start Voice Session</button>
        </div>
      ) : (
        <div className="session-active">
          <div className="session-status">
            <span>Connected: {sessionStatus.connected ? 'Yes' : 'No'}</span>
            <span>Participants: {sessionStatus.participantCount}</span>
            <span>Duration: {Math.floor(sessionStatus.duration / 60)}:{(sessionStatus.duration % 60).toString().padStart(2, '0')}</span>
            <span>Latency: {latency}ms</span>
          </div>

          {room && <AudioVisualizer room={room} />}

          <div className="transcription">
            <h2>Transcription</h2>
            {transcription.map((msg) => (
              <div key={msg.id} className={`message ${msg.speaker}`}>
                <span className="speaker">{msg.speaker === 'user' ? 'You' : 'Agent'}:</span>
                <span className="text">{msg.text}</span>
                {!msg.isFinal && <span className="interim">(interim)</span>}
              </div>
            ))}
          </div>

          <button onClick={handleEnd} className="end-session">End Session</button>
        </div>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  );
};
```

## 8. UI/UX Design

### 8.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│  Header                                                  │
│  [Logo] [Nav: Dashboard | Chat | Voice | Meals |        │
│         Workouts] [Profile] [Logout]                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Main Content Area                                       │
│  (Page-specific content)                                 │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Footer                                                  │
│  © 2024 Shuren | Testing Interface                      │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Key Screen Wireframes

#### Dashboard
```
┌─────────────────────────────────────────────────────────┐
│  Welcome back, [User]!                                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Profile Summary │  │ Meal Plan       │              │
│  │                 │  │                 │              │
│  │ Fitness: Inter. │  │ 2000 cal/day    │              │
│  │ Goal: Fat Loss  │  │ P: 150g C: 200g │              │
│  │ Energy: High    │  │ F: 60g          │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Workout Sched.  │  │ Quick Actions   │              │
│  │                 │  │                 │              │
│  │ 3x/week         │  │ [Start Chat]    │              │
│  │ Mon, Wed, Fri   │  │ [Voice Session] │              │
│  │ 7:00 AM         │  │ [View Meals]    │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

#### Chat Page
```
┌─────────────────────────────────────────────────────────┐
│  Agent: [Dropdown: General Assistant ▼]                 │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │ Message History                                   │  │
│  │                                                   │  │
│  │ You: What should I eat for breakfast?            │  │
│  │                                                   │  │
│  │ Agent: Based on your meal plan, I recommend...   │  │
│  │                                                   │  │
│  │ You: Can I substitute eggs?                      │  │
│  │                                                   │  │
│  │ Agent: Yes, you can substitute with...           │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ Type your message...                    [Send]   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Voice Session Page
```
┌─────────────────────────────────────────────────────────┐
│  Voice Session                                           │
├─────────────────────────────────────────────────────────┤
│  Agent: [Dropdown: Workout Planning ▼]                  │
│                                                          │
│  [Start Voice Session]                                   │
│                                                          │
│  OR (when connected):                                    │
│                                                          │
│  Status: Connected | Participants: 2 | Duration: 1:23   │
│  Latency: 120ms                                          │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 🎤 Voice Activity Indicator                       │  │
│  │ [Waveform visualization]                          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  Transcription:                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ You: What exercises should I do today?           │  │
│  │ Agent: Today is leg day. Let's start with...     │  │
│  │ You: How many sets?                              │  │
│  │ Agent: I recommend 3 sets of 10 reps...          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  [End Session]                                           │
└─────────────────────────────────────────────────────────┘
```

#### Onboarding Progress
```
┌─────────────────────────────────────────────────────────┐
│  Onboarding - Step 3 of 12                              │
│  ●●●○○○○○○○○○                                           │
├─────────────────────────────────────────────────────────┤
│  Physical Constraints                                    │
│                                                          │
│  Do you have any equipment limitations?                  │
│  ☐ No gym access                                        │
│  ☐ Limited equipment                                    │
│  ☐ Full gym access                                      │
│                                                          │
│  Do you have any injuries or limitations?                │
│  [Text area for description]                             │
│                                                          │
│  [Back]                              [Next]              │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Color Scheme & Typography

**Colors:**
- Primary: #3B82F6 (Blue)
- Secondary: #10B981 (Green)
- Accent: #F59E0B (Amber)
- Background: #F9FAFB (Light Gray)
- Text: #111827 (Dark Gray)
- Error: #EF4444 (Red)
- Success: #10B981 (Green)

**Typography:**
- Font Family: Inter (sans-serif)
- Headings: 600 weight
- Body: 400 weight
- Small text: 14px
- Body text: 16px
- Headings: 20px, 24px, 32px

### 8.4 Responsive Breakpoints

- Mobile: < 640px (single column, stacked layout)
- Tablet: 640px - 1024px (2-column grid)
- Desktop: > 1024px (3-column grid, sidebar navigation)

## 9. Error Handling Strategy

### 9.1 Error Types

**Network Errors:**
- Connection timeout
- Server unreachable
- Request failed

**Authentication Errors:**
- 401 Unauthorized (token expired/invalid)
- 403 Forbidden (insufficient permissions)

**Validation Errors:**
- 422 Unprocessable Entity (invalid input)
- Field-level validation errors

**Server Errors:**
- 500 Internal Server Error
- 503 Service Unavailable

**LiveKit Errors:**
- Connection failed
- Microphone permission denied
- Room join failed
- Agent not responding

### 9.2 Error Handling Patterns


```typescript
// Error handling utility
export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export const handleApiError = (error: any): AppError => {
  if (error.response) {
    // Server responded with error
    const { status, data } = error.response;
    
    if (status === 401) {
      return new AppError(
        'Authentication required. Please log in.',
        'AUTH_REQUIRED',
        401
      );
    }
    
    if (status === 403) {
      return new AppError(
        'You do not have permission to perform this action.',
        'FORBIDDEN',
        403
      );
    }
    
    if (status === 422) {
      return new AppError(
        'Validation failed. Please check your input.',
        'VALIDATION_ERROR',
        422,
        data.detail
      );
    }
    
    if (status >= 500) {
      return new AppError(
        'Server error. Please try again later.',
        'SERVER_ERROR',
        status
      );
    }
    
    return new AppError(
      data.message || 'An error occurred',
      'API_ERROR',
      status,
      data
    );
  }
  
  if (error.request) {
    // Request made but no response
    return new AppError(
      'Unable to reach server. Please check your connection.',
      'NETWORK_ERROR'
    );
  }
  
  // Something else happened
  return new AppError(
    error.message || 'An unexpected error occurred',
    'UNKNOWN_ERROR'
  );
};

// Usage in components
try {
  await chatService.sendMessage(message, agentType);
} catch (error) {
  const appError = handleApiError(error);
  setError(appError.message);
  
  // Log for debugging
  console.error('Chat error:', appError);
}
```

### 9.3 User-Facing Error Messages

**Network Errors:**
- "Unable to connect to server. Please check your internet connection."
- "Request timed out. Please try again."

**Authentication Errors:**
- "Your session has expired. Please log in again."
- "Invalid credentials. Please check your email and password."

**Validation Errors:**
- "Please fill in all required fields."
- "Invalid email format."
- "Password must be at least 8 characters."

**Voice Session Errors:**
- "Microphone access denied. Please enable microphone permissions."
- "Failed to connect to voice session. Please try again."
- "Voice session ended unexpectedly. Reconnecting..."

### 9.4 Error Recovery Strategies

**Automatic Retry:**
- Network errors: Retry up to 3 times with exponential backoff
- Voice connection: Automatic reconnection attempt

**User-Initiated Retry:**
- Display "Try Again" button for failed operations
- Clear error state on retry

**Graceful Degradation:**
- If streaming chat fails, fall back to regular chat
- If voice session fails, suggest text chat alternative

**Error Logging:**
- Log all errors to console in development
- Send critical errors to monitoring service in production

## 10. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before writing the correctness properties, I need to analyze the acceptance criteria to determine which are testable as properties, examples, or edge cases.



### Property Reflection

After analyzing all testable acceptance criteria, I identified the following potential redundancies:
- Properties 2.4.2 (send messages) and 2.4.4 (agent selection) both test message routing - these can be combined into a single property that validates messages are sent to the correct agent type
- All other properties provide unique validation value and should be kept

### Correctness Properties

Property 1: Valid registration creates authenticated session
*For any* valid email and password combination, submitting registration should result in a successful API call, JWT token storage, and authenticated state.
**Validates: Requirements 2.1.1**

Property 2: Valid credentials authenticate user
*For any* valid email and password credentials, submitting login should result in a successful API call, JWT token storage, and authenticated state.
**Validates: Requirements 2.1.2**

Property 3: JWT token included in authenticated requests
*For any* authenticated API request, the Authorization header should contain the stored JWT token.
**Validates: Requirements 2.1.3**

Property 4: Protected routes require authentication
*For any* protected route, attempting to access without a valid token should result in redirect to the login page.
**Validates: Requirements 2.1.5**

Property 5: Onboarding steps persist data
*For any* onboarding step (1-12) with valid data, submitting the step should result in an API call to save the data and successful response.
**Validates: Requirements 2.2.2**

Property 6: Backward navigation in onboarding
*For any* onboarding step greater than 1, clicking the back button should navigate to the previous step (step - 1).
**Validates: Requirements 2.2.3**

Property 7: Validation errors displayed
*For any* API validation error (422 response), the error details should be displayed in the UI with clear messaging.
**Validates: Requirements 2.2.6**

Property 8: Messages routed to selected agent
*For any* text message and selected agent type, the message should be sent to the backend with the correct agent_type parameter and receive a response from that agent.
**Validates: Requirements 2.4.2, 2.4.4**

Property 9: Chat history accumulates messages
*For any* sequence of N messages sent during a session, the chat history should contain exactly N user messages and N agent responses (or N-1 if last response pending).
**Validates: Requirements 2.4.5**

Property 10: Chat errors displayed
*For any* chat API error, an error message should be displayed in the UI and the chat interface should remain functional.
**Validates: Requirements 2.4.7**

Property 11: Dish search filters results
*For any* search query string, the search should call the API with the query parameter and display only dishes matching the search criteria.
**Validates: Requirements 2.5.3**

Property 12: Shopping list groups by category
*For any* shopping list generated from meals, ingredients should be grouped by category with quantities aggregated across meals.
**Validates: Requirements 2.5.6**

Property 13: Workout set logging persists
*For any* exercise set with reps and weight data, logging the set should result in an API call with the correct exercise ID, set number, reps, and weight.
**Validates: Requirements 2.6.3**

Property 14: Transcription updates from LiveKit data
*For any* transcription data received from the LiveKit room, the transcription state should be updated with the new message including speaker, text, and timestamp.
**Validates: Requirements 2.7.5**

Property 15: Session status reflects LiveKit events
*For any* LiveKit room event (connected, disconnected, participant joined/left), the session status should update to reflect the current connection state and participant count.
**Validates: Requirements 2.7.7**

Property 16: Voice connection errors handled
*For any* LiveKit connection error (permission denied, connection failed, room join failed), an error message should be displayed and the session should remain in a recoverable state.
**Validates: Requirements 2.7.9**

Property 17: Latency updates from agent data
*For any* latency data received from the agent via LiveKit data channel, the latency indicator should update to display the current response time.
**Validates: Requirements 2.7.10**

## 11. Testing Strategy

### 11.1 Testing Approach

The frontend will use a dual testing approach combining unit tests for specific examples and property-based tests for universal properties.

**Unit Tests:**
- Specific user flows (login, logout, profile unlock)
- Edge cases (empty inputs, invalid formats)
- Error conditions (network failures, validation errors)
- Component rendering with specific props
- Service layer functions with mock data

**Property-Based Tests:**
- Universal properties across all inputs (see Correctness Properties above)
- Input validation across random valid/invalid data
- State management consistency
- API integration with various response types

### 11.2 Testing Tools

**Framework:** Vitest (latest)
- Fast, Vite-native test runner
- Compatible with Jest API
- Built-in TypeScript support

**Testing Library:** React Testing Library (latest)
- User-centric testing approach
- Encourages accessibility best practices
- Avoids implementation details

**Property-Based Testing:** fast-check (latest)
- JavaScript/TypeScript property-based testing library
- Generates random test cases
- Shrinks failing cases to minimal examples

**Mocking:** MSW (Mock Service Worker, latest)
- Intercepts network requests
- Provides realistic API mocking
- Works in both tests and browser

**LiveKit Testing:** Mock LiveKit SDK
- Mock Room and Track objects
- Simulate connection events
- Test without actual LiveKit server

### 11.3 Test Organization

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── LoginForm.test.tsx
│   │   ├── chat/
│   │   │   ├── MessageList.tsx
│   │   │   └── MessageList.test.tsx
│   │   └── ...
│   ├── services/
│   │   ├── authService.ts
│   │   └── authService.test.ts
│   ├── hooks/
│   │   ├── useVoiceSession.ts
│   │   └── useVoiceSession.test.ts
│   └── ...
└── tests/
    ├── properties/
    │   ├── auth.properties.test.ts
    │   ├── chat.properties.test.ts
    │   ├── voice.properties.test.ts
    │   └── ...
    ├── integration/
    │   ├── onboarding-flow.test.ts
    │   ├── chat-flow.test.ts
    │   └── ...
    └── setup.ts
```

### 11.4 Property-Based Test Configuration

Each property test will:
- Run minimum 100 iterations (due to randomization)
- Reference the design document property number
- Use descriptive test names matching property titles
- Tag format: `Feature: minimal-frontend-testing, Property {number}: {property_text}`

Example property test:
```typescript
// tests/properties/auth.properties.test.ts
import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { authService } from '../../src/services/authService';

describe('Auth Properties', () => {
  it('Property 3: JWT token included in authenticated requests', async () => {
    // Feature: minimal-frontend-testing, Property 3: JWT token included in authenticated requests
    
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 10 }), // Random JWT token
        fc.constantFrom('GET', 'POST', 'PUT', 'DELETE'), // Random HTTP method
        async (token, method) => {
          // Set token
          authService.setToken(token);
          
          // Make authenticated request
          const config = api.defaults;
          const requestConfig = await api.interceptors.request.handlers[0].fulfilled({
            method,
            headers: {},
          });
          
          // Verify token is in Authorization header
          expect(requestConfig.headers.Authorization).toBe(`Bearer ${token}`);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### 11.5 Unit Test Patterns

**Component Tests:**
```typescript
// src/components/auth/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('should display validation error for invalid email', async () => {
    render(<LoginForm />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /log in/i });
    
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });
  });
  
  it('should call login service on valid submission', async () => {
    const mockLogin = vi.fn().mockResolvedValue({ token: 'abc123' });
    
    render(<LoginForm onLogin={mockLogin} />);
    
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /log in/i }));
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });
});
```

**Service Tests:**
```typescript
// src/services/authService.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { authService } from './authService';

const server = setupServer();

beforeEach(() => server.listen());
afterEach(() => server.resetHandlers());

describe('AuthService', () => {
  it('should store token after successful login', async () => {
    server.use(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          access_token: 'test-token-123',
          token_type: 'bearer',
          user: { id: '1', email: 'test@example.com' },
        });
      })
    );
    
    const result = await authService.login('test@example.com', 'password');
    
    expect(result.access_token).toBe('test-token-123');
    expect(authService.getToken()).toBe('test-token-123');
  });
});
```

### 11.6 Integration Test Examples

**Onboarding Flow:**
```typescript
// tests/integration/onboarding-flow.test.ts
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { OnboardingPage } from '../../src/pages/OnboardingPage';

describe('Onboarding Flow', () => {
  it('should complete full onboarding flow', async () => {
    render(<OnboardingPage />);
    
    // Step 1: Fitness Level
    expect(screen.getByText(/step 1 of 12/i)).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/intermediate/i));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    
    // Step 2: Goals
    await waitFor(() => {
      expect(screen.getByText(/step 2 of 12/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByLabelText(/fat loss/i));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    
    // ... continue through all 12 steps
    
    // Step 12: Confirmation
    await waitFor(() => {
      expect(screen.getByText(/step 12 of 12/i)).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /complete/i }));
    
    // Should redirect to dashboard
    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard');
    });
  });
});
```

### 11.7 Test Coverage Goals

- **Overall Coverage:** 70%+ (this is a testing interface, not production)
- **Critical Paths:** 90%+ (auth, onboarding, chat, voice)
- **Service Layer:** 80%+ (API integration is critical)
- **Components:** 60%+ (focus on logic, not just rendering)
- **Hooks:** 80%+ (custom hooks contain important logic)

### 11.8 Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run only unit tests
npm run test:unit

# Run only property tests
npm run test:properties

# Run only integration tests
npm run test:integration

# Run specific test file
npm run test src/services/authService.test.ts
```

### 11.9 CI/CD Integration

Tests should run automatically on:
- Pull requests
- Commits to main branch
- Pre-deployment checks

Minimum requirements for passing:
- All tests pass
- Coverage >= 70% overall
- No critical linting errors

## 12. Performance Considerations

### 12.1 Code Splitting

```typescript
// Lazy load pages for faster initial load
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const VoicePage = lazy(() => import('./pages/VoicePage'));
const MealsPage = lazy(() => import('./pages/MealsPage'));
const WorkoutsPage = lazy(() => import('./pages/WorkoutsPage'));

// Use Suspense for loading states
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/chat" element={<ChatPage />} />
    {/* ... */}
  </Routes>
</Suspense>
```

### 12.2 Caching Strategy

**Profile Data:**
- Cache in UserContext after first load
- Refresh only on explicit user action (unlock, edit)
- TTL: Session duration

**Chat History:**
- Store in component state during session
- Clear on page navigation
- No persistence needed (testing interface)

**Meal/Workout Data:**
- Fetch on page load
- Cache for 5 minutes
- Invalidate on user actions (log workout, request substitution)

### 12.3 Optimizations

**Debounced Search:**
```typescript
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    mealService.searchDishes(query).then(setResults);
  }, 300),
  []
);
```

**Optimistic UI Updates:**
```typescript
// Immediately update UI, rollback on error
const logSet = async (setData: WorkoutLog) => {
  // Optimistically update UI
  setExercises(prev => updateSetInExercises(prev, setData));
  
  try {
    await workoutService.logSet(setData);
  } catch (error) {
    // Rollback on error
    setExercises(prev => rollbackSetUpdate(prev, setData));
    showError('Failed to log set');
  }
};
```

**Virtualized Lists:**
- Use react-window for long lists (meal history, workout history)
- Render only visible items
- Improves performance with 100+ items

## 13. Security Considerations

### 13.1 Authentication Security

**Token Storage:**
- Store JWT in localStorage (acceptable for testing interface)
- Clear token on logout
- Validate token expiration client-side

**HTTPS:**
- Use HTTPS in production
- Secure WebSocket connections (wss://)

### 13.2 Input Validation

**Client-Side Validation:**
- Validate all form inputs before submission
- Sanitize user input to prevent XSS
- Use TypeScript for type safety

**Server-Side Validation:**
- Always validate on backend (client validation is UX only)
- Display backend validation errors clearly

### 13.3 API Security

**CORS:**
- Backend should configure CORS properly
- Only allow frontend origin

**Rate Limiting:**
- Backend should implement rate limiting
- Frontend should handle 429 responses gracefully

## 14. Deployment

### 14.1 Environment Variables

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_LIVEKIT_URL=ws://localhost:7880

# .env.production
VITE_API_BASE_URL=https://api.shuren.example.com/api/v1
VITE_LIVEKIT_URL=wss://livekit.shuren.example.com
```

### 14.2 Build Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'livekit': ['livekit-client', '@livekit/components-react'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### 14.3 Deployment Options

**Development:**
```bash
npm run dev
# Runs on http://localhost:3000
```

**Production Build:**
```bash
npm run build
npm run preview
```

**Deployment Platforms:**
- Vercel (recommended for quick deployment)
- Netlify
- AWS S3 + CloudFront
- DigitalOcean App Platform

### 14.4 Backend Requirements

Before deploying frontend:
1. Backend must be running and accessible
2. CORS configured to allow frontend origin
3. LiveKit server accessible
4. Database seeded with test data
5. All Phase 1 & 2 endpoints functional

## 15. Future Enhancements

After MVP validation:

1. **Enhanced Voice UI:**
   - Waveform visualization
   - Voice activity animation
   - Recording playback

2. **Real-Time Features:**
   - WebSocket for live updates
   - Push notifications (Phase 3)
   - Real-time workout tracking

3. **Advanced UI/UX:**
   - Dark mode
   - Animations and transitions
   - Gesture controls for mobile

4. **Analytics:**
   - Progress charts and graphs
   - Trend analysis
   - Performance metrics

5. **Offline Support:**
   - Service worker for offline access
   - Local data caching
   - Sync when online

6. **Mobile Optimization:**
   - Progressive Web App (PWA)
   - Native-like experience
   - Install prompt

7. **Accessibility:**
   - Screen reader optimization
   - Keyboard navigation improvements
   - High contrast mode

8. **Developer Tools:**
   - Agent performance dashboard
   - API request inspector
   - Error tracking integration

## 16. Conclusion

This design document provides a comprehensive blueprint for building a minimal React frontend to test the Shuren AI backend. The architecture emphasizes:

- **Clean separation of concerns** (pages, components, services, contexts)
- **Type safety** with TypeScript throughout
- **Testability** with property-based and unit testing strategies
- **Maintainability** with clear patterns and conventions
- **Extensibility** for future enhancements

The frontend will enable thorough testing of all Phase 1 & 2 backend functionality including authentication, onboarding, AI agent interactions (text and voice), meal management, and workout tracking.

