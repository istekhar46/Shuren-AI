# Design Document: Frontend-Backend API Alignment

## Overview

This design document specifies the frontend architecture and implementation patterns required to integrate with the validated backend onboarding system. The frontend will implement a React-based (or similar framework) single-page application that enforces mandatory onboarding, manages user state, routes API requests correctly, and provides rich visual feedback throughout the user journey.

The design focuses on three core areas:
1. **State Management**: Tracking onboarding status and user authentication state
2. **API Integration**: Correct endpoint routing and error handling
3. **UI Components**: Navigation locks, progress indicators, and chat interface

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Auth       │  │  Onboarding  │  │   Main App   │      │
│  │   Module     │  │   Module     │  │   Module     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │  State Manager  │                        │
│                   │  (Redux/Zustand)│                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   API Client    │                        │
│                   └────────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Backend API    │
                    │  (FastAPI)      │
                    └─────────────────┘
```

### Component Hierarchy

```
App
├── AuthProvider
│   ├── LoginPage
│   └── RegisterPage
├── OnboardingGuard (Route Guard)
│   ├── OnboardingPage
│   │   ├── ProgressIndicator
│   │   ├── ChatInterface
│   │   │   ├── MessageList
│   │   │   ├── MessageInput
│   │   │   └── LoadingIndicator
│   │   └── WelcomeMessage
│   └── MainApp (Protected)
│       ├── NavigationMenu (with locks)
│       ├── ChatPage
│       ├── DashboardPage
│       ├── ProfilePage
│       └── SettingsPage
```

## Components and Interfaces

### 1. State Management

#### User State Interface

```typescript
interface UserState {
  id: string;
  email: string;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

interface OnboardingProgress {
  current_state: number;
  total_states: number;
  completed_states: number[];
  completion_percentage: number;
  is_complete: boolean;
  can_complete: boolean;
}

interface StateMetadata {
  state_number: number;
  name: string;
  agent: string;
  description: string;
  required_fields: string[];
}

interface AppState {
  user: UserState | null;
  isAuthenticated: boolean;
  onboardingProgress: OnboardingProgress | null;
  stateMetadata: Record<number, StateMetadata>;
  currentChatMessages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}
```

#### State Management Actions

```typescript
// Authentication actions
type AuthAction =
  | { type: 'LOGIN_SUCCESS'; payload: UserState }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: Partial<UserState> };

// Onboarding actions
type OnboardingAction =
  | { type: 'LOAD_PROGRESS'; payload: OnboardingProgress }
  | { type: 'UPDATE_STATE'; payload: number }
  | { type: 'COMPLETE_ONBOARDING' }
  | { type: 'LOAD_METADATA'; payload: Record<number, StateMetadata> };

// Chat actions
type ChatAction =
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_MESSAGES' };
```

### 2. API Client

#### API Client Interface

```typescript
interface APIClient {
  // Authentication
  login(email: string, password: string): Promise<LoginResponse>;
  register(email: string, password: string): Promise<RegisterResponse>;
  logout(): Promise<void>;
  
  // User
  getCurrentUser(): Promise<UserState>;
  
  // Onboarding
  getOnboardingProgress(): Promise<OnboardingProgress>;
  sendOnboardingMessage(message: string, currentState: number): Promise<OnboardingChatResponse>;
  
  // Chat
  sendChatMessage(message: string): Promise<ChatResponse>;
  getChatHistory(limit?: number): Promise<ChatHistoryResponse>;
  deleteChatHistory(): Promise<void>;
}
```

#### Request/Response Types

```typescript
interface ChatRequest {
  message: string;
  agent_type?: string;
}

interface ChatResponse {
  response: string;
  agent_type: string;
  conversation_id: string;
  tools_used: string[];
}

interface OnboardingChatRequest {
  message: string;
  current_state: number;
}

interface OnboardingChatResponse {
  response: string;
  agent_type: string;
  state_updated: boolean;
  new_state: number | null;
  progress: OnboardingProgress;
}

interface ErrorResponse {
  message: string;
  error_code: string;
  redirect?: string;
  onboarding_progress?: {
    current_state: number;
    completion_percentage: number;
  };
}
```

#### API Client Implementation Pattern

```typescript
class APIClient {
  private baseURL: string;
  private authToken: string | null;
  
  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.authToken = this.loadToken();
  }
  
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers = {
      'Content-Type': 'application/json',
      ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` }),
      ...options.headers,
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new APIError(response.status, error);
    }
    
    return response.json();
  }
  
  async sendOnboardingMessage(
    message: string,
    currentState: number
  ): Promise<OnboardingChatResponse> {
    return this.request<OnboardingChatResponse>('/api/v1/chat/onboarding', {
      method: 'POST',
      body: JSON.stringify({ message, current_state: currentState }),
    });
  }
  
  async sendChatMessage(message: string): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
}
```

### 3. Route Guard Component

#### OnboardingGuard Implementation

```typescript
interface OnboardingGuardProps {
  children: React.ReactNode;
}

const OnboardingGuard: React.FC<OnboardingGuardProps> = ({ children }) => {
  const { user, onboardingProgress } = useAppState();
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    // If not authenticated, redirect to login
    if (!user) {
      navigate('/login', { state: { from: location } });
      return;
    }
    
    // If onboarding not completed, redirect to onboarding
    if (!user.onboarding_completed) {
      if (location.pathname !== '/onboarding') {
        navigate('/onboarding');
      }
      return;
    }
    
    // If onboarding completed but on onboarding page, redirect to main app
    if (user.onboarding_completed && location.pathname === '/onboarding') {
      navigate('/chat');
    }
  }, [user, location, navigate]);
  
  // Show loading while checking auth state
  if (!user) {
    return <LoadingScreen />;
  }
  
  // Render children if checks pass
  return <>{children}</>;
};
```

### 4. Progress Indicator Component

#### ProgressIndicator Interface

```typescript
interface ProgressIndicatorProps {
  currentState: number;
  totalStates: number;
  completedStates: number[];
  stateMetadata: Record<number, StateMetadata>;
  onStateClick?: (state: number) => void;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  currentState,
  totalStates,
  completedStates,
  stateMetadata,
  onStateClick,
}) => {
  const completionPercentage = (completedStates.length / totalStates) * 100;
  
  return (
    <div className="progress-indicator">
      <div className="progress-header">
        <h3>Onboarding Progress</h3>
        <span>Step {currentState} of {totalStates}</span>
      </div>
      
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${completionPercentage}%` }}
        />
      </div>
      
      <div className="state-list">
        {Array.from({ length: totalStates }, (_, i) => i + 1).map((stateNum) => {
          const metadata = stateMetadata[stateNum];
          const isCompleted = completedStates.includes(stateNum);
          const isCurrent = stateNum === currentState;
          const isUpcoming = stateNum > currentState;
          
          return (
            <div
              key={stateNum}
              className={`state-item ${
                isCompleted ? 'completed' : ''
              } ${isCurrent ? 'current' : ''} ${
                isUpcoming ? 'upcoming' : ''
              }`}
              onClick={() => onStateClick?.(stateNum)}
            >
              <div className="state-icon">
                {isCompleted ? '✓' : stateNum}
              </div>
              <div className="state-info">
                <div className="state-name">{metadata?.name}</div>
                <div className="state-description">{metadata?.description}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

### 5. Chat Interface Component

#### ChatInterface Implementation

```typescript
interface ChatInterfaceProps {
  mode: 'onboarding' | 'regular';
  currentState?: number;
  onStateUpdate?: (newState: number) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  mode,
  currentState,
  onStateUpdate,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const apiClient = useAPIClient();
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) {
      return;
    }
    
    // Add user message to UI
    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    try {
      if (mode === 'onboarding' && currentState) {
        const response = await apiClient.sendOnboardingMessage(
          inputValue,
          currentState
        );
        
        // Add assistant message
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          agent_type: response.agent_type,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        
        // Handle state update
        if (response.state_updated && response.new_state) {
          onStateUpdate?.(response.new_state);
          
          // Show transition message
          const transitionMessage: ChatMessage = {
            role: 'system',
            content: `✓ Progress saved! Moving to step ${response.new_state}...`,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, transitionMessage]);
        }
        
        // Check if onboarding complete
        if (response.progress.is_complete) {
          const completionMessage: ChatMessage = {
            role: 'system',
            content: '🎉 Onboarding complete! Redirecting to main app...',
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, completionMessage]);
          
          setTimeout(() => {
            window.location.href = '/chat';
          }, 3000);
        }
      } else {
        const response = await apiClient.sendChatMessage(inputValue);
        
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          agent_type: response.agent_type,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      if (error instanceof APIError) {
        handleAPIError(error);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'system',
            content: 'An error occurred. Please try again.',
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleAPIError = (error: APIError) => {
    if (error.status === 403) {
      const errorData = error.data as ErrorResponse;
      
      if (errorData.error_code === 'ONBOARDING_REQUIRED') {
        window.location.href = errorData.redirect || '/onboarding';
      } else if (errorData.error_code === 'AGENT_NOT_ALLOWED') {
        setMessages((prev) => [
          ...prev,
          {
            role: 'system',
            content: errorData.message,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } else if (error.status === 400) {
      // State mismatch - resync
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: 'Syncing your progress...',
          timestamp: new Date().toISOString(),
        },
      ]);
      // Trigger progress refresh
      window.location.reload();
    }
  };
  
  return (
    <div className="chat-interface">
      <MessageList messages={messages} />
      <MessageInput
        value={inputValue}
        onChange={setInputValue}
        onSend={handleSendMessage}
        disabled={isLoading}
        placeholder={
          mode === 'onboarding'
            ? 'Type your response...'
            : 'Ask me anything about your fitness journey...'
        }
      />
      {isLoading && <LoadingIndicator />}
    </div>
  );
};
```

### 6. Navigation Menu Component

#### NavigationMenu with Locks

```typescript
interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: React.ReactNode;
  requiresOnboarding: boolean;
}

const navigationItems: NavigationItem[] = [
  { id: 'chat', label: 'Chat', path: '/chat', icon: <ChatIcon />, requiresOnboarding: true },
  { id: 'dashboard', label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon />, requiresOnboarding: true },
  { id: 'workouts', label: 'Workouts', path: '/workouts', icon: <WorkoutIcon />, requiresOnboarding: true },
  { id: 'meals', label: 'Meals', path: '/meals', icon: <MealIcon />, requiresOnboarding: true },
  { id: 'profile', label: 'Profile', path: '/profile', icon: <ProfileIcon />, requiresOnboarding: true },
];

const NavigationMenu: React.FC = () => {
  const { user } = useAppState();
  const navigate = useNavigate();
  const location = useLocation();
  
  const handleNavClick = (item: NavigationItem) => {
    if (item.requiresOnboarding && !user?.onboarding_completed) {
      // Show tooltip or toast
      return;
    }
    navigate(item.path);
  };
  
  return (
    <nav className="navigation-menu">
      {navigationItems.map((item) => {
        const isLocked = item.requiresOnboarding && !user?.onboarding_completed;
        const isActive = location.pathname === item.path;
        
        return (
          <Tooltip
            key={item.id}
            content={isLocked ? 'Complete onboarding to unlock this feature' : ''}
            disabled={!isLocked}
          >
            <button
              className={`nav-item ${isActive ? 'active' : ''} ${isLocked ? 'locked' : ''}`}
              onClick={() => handleNavClick(item)}
              disabled={isLocked}
              aria-label={item.label}
              aria-disabled={isLocked}
            >
              {item.icon}
              <span>{item.label}</span>
              {isLocked && <LockIcon className="lock-icon" />}
            </button>
          </Tooltip>
        );
      })}
    </nav>
  );
};
```

## Data Models

### Local Storage Schema

```typescript
// Stored in localStorage or sessionStorage
interface StoredAuthData {
  token: string;
  refreshToken?: string;
  expiresAt: number;
}

interface CachedProgress {
  data: OnboardingProgress;
  cachedAt: number;
  ttl: number; // 30 seconds
}
```

### Cache Management

```typescript
class CacheManager {
  private cache: Map<string, { data: any; expiresAt: number }>;
  
  constructor() {
    this.cache = new Map();
  }
  
  set(key: string, data: any, ttlSeconds: number): void {
    const expiresAt = Date.now() + ttlSeconds * 1000;
    this.cache.set(key, { data, expiresAt });
  }
  
  get<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    if (Date.now() > cached.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data as T;
  }
  
  invalidate(key: string): void {
    this.cache.delete(key);
  }
  
  clear(): void {
    this.cache.clear();
  }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Navigation Lock State Consistency
*For any* user state, the navigation menu items should be disabled if and only if onboarding_completed is false, and all items should be enabled if and only if onboarding_completed is true.
**Validates: Requirements 1.1, 7.1**

### Property 2: Locked Navigation Tooltip Display
*For any* navigation item that is locked (user has incomplete onboarding), hovering over the item should display a tooltip containing the text "Complete onboarding to unlock this feature".
**Validates: Requirements 1.2**

### Property 3: Protected Route Redirection
*For any* protected route and any user with onboarding_completed=false, attempting to navigate to that route should result in a redirect to /onboarding with an appropriate message.
**Validates: Requirements 1.3**

### Property 4: Onboarding Completion Reactivity
*For any* user state transition where onboarding_completed changes from false to true, all navigation items should become enabled without requiring a page refresh.
**Validates: Requirements 1.4**

### Property 5: Progress Indicator Correctness
*For any* valid onboarding state (1-9) and any set of completed states, the progress indicator should display "Step X of 9", show checkmarks for all completed states, highlight the current state with distinct styling, and show upcoming states in grayed-out styling.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 6: State Metadata Display
*For any* state metadata object fetched from the backend, the UI should render the state name and description fields for each state in the progress indicator.
**Validates: Requirements 2.5**

### Property 7: State Transition Animation
*For any* state transition (current_state changes), the progress indicator should animate the transition and update to reflect the new state.
**Validates: Requirements 2.6**

### Property 8: Endpoint Routing Based on Onboarding Status
*For any* chat message, if the user has onboarding_completed=false, the message should be sent to POST /api/v1/chat/onboarding; if onboarding_completed=true, the message should be sent to POST /api/v1/chat.
**Validates: Requirements 3.1, 3.2, 7.2**

### Property 9: Onboarding Required Error Handling
*For any* 403 error response with error_code "ONBOARDING_REQUIRED", the frontend should redirect to the path specified in the redirect field and display the message from the response.
**Validates: Requirements 1.5, 3.3, 6.1**

### Property 10: Onboarding Complete Error Handling
*For any* 403 error from POST /api/v1/chat/onboarding indicating onboarding is already complete, the frontend should redirect to the main chat interface.
**Validates: Requirements 3.4**

### Property 11: Current State Payload Inclusion
*For any* message sent to POST /api/v1/chat/onboarding, the request payload should include a current_state field that matches the user's current onboarding step stored in local state.
**Validates: Requirements 3.5**

### Property 12: State Mismatch Recovery
*For any* 400 error response indicating state mismatch, the frontend should fetch the current state from GET /api/v1/onboarding/progress, display "Syncing your progress...", and update local state.
**Validates: Requirements 3.6, 6.3**

### Property 13: Message Role Styling
*For any* message displayed in the chat interface, if the role is "user" it should have user styling, if the role is "assistant" it should have assistant styling, and if the role is "system" it should have system styling.
**Validates: Requirements 4.2, 4.3**

### Property 14: State Update Confirmation
*For any* API response where state_updated is true, the frontend should display a confirmation message indicating progress to the next state.
**Validates: Requirements 4.4**

### Property 15: Local State Synchronization
*For any* API response where state_updated is true and new_state is provided, the frontend should update the local current_state to match new_state for all subsequent requests.
**Validates: Requirements 4.5, 5.6**

### Property 16: Progress Indicator Update
*For any* API response containing progress information, the progress indicator should update to reflect the completion_percentage from the response.
**Validates: Requirements 4.6**

### Property 17: Onboarding Completion Flow
*For any* API response where progress.is_complete is true, the frontend should display a completion message and redirect to the main application after 3 seconds.
**Validates: Requirements 4.7**

### Property 18: Post-Login Onboarding Check
*For any* user after successful login, if onboarding_completed is false, the frontend should redirect to /onboarding; if onboarding_completed is true, the frontend should allow access to the main application.
**Validates: Requirements 5.2, 5.3**

### Property 19: Progress Completion Redirect
*For any* progress response where is_complete is true, the frontend should redirect to the main application.
**Validates: Requirements 5.5**

### Property 20: State Recovery After Refresh
*For any* page refresh during onboarding, the frontend should fetch the current state from the API and resume from that state without losing progress.
**Validates: Requirements 5.7**

### Property 21: Agent Not Allowed Error Handling
*For any* 403 error with error_code "AGENT_NOT_ALLOWED", the frontend should display an error message explaining that only the general agent is available.
**Validates: Requirements 6.2**

### Property 22: Server Error Handling
*For any* 500 error response, the frontend should display a user-friendly error message and provide a retry button.
**Validates: Requirements 6.4**

### Property 23: Offline Message Queueing
*For any* network connectivity loss during onboarding, the frontend should display an offline indicator and queue messages for retry; when connectivity is restored, queued messages should be automatically sent.
**Validates: Requirements 6.5, 6.6**

### Property 24: Post-Onboarding Agent Type Omission
*For any* chat request sent by a user with onboarding_completed=true, the request payload should not include an agent_type field.
**Validates: Requirements 7.3**

### Property 25: Agent Type Display
*For any* response from POST /api/v1/chat, the frontend should display the agent_type value in the chat interface.
**Validates: Requirements 7.4**

### Property 26: Completed User Onboarding Redirect
*For any* user with onboarding_completed=true attempting to access /onboarding, the frontend should redirect to the main chat interface with the message "You've already completed onboarding".
**Validates: Requirements 7.5**

### Property 27: Responsive Layout Adaptation
*For any* screen width, if below mobile breakpoint (768px), the progress indicator should use a compact vertical layout; if above desktop breakpoint (1024px), the progress indicator should use a sidebar layout with full state names.
**Validates: Requirements 8.1, 8.2**

### Property 28: Keyboard Navigation Support
*For all* interactive elements in the onboarding interface, tab navigation should move focus through elements in logical order.
**Validates: Requirements 8.3**

### Property 29: Screen Reader Announcements
*For any* progress update or state transition, the frontend should announce the change via ARIA live regions for screen reader users.
**Validates: Requirements 8.4**

### Property 30: Mobile Keyboard Visibility
*For any* focus event on the chat input on mobile devices, the viewport should scroll to ensure the input remains visible above the keyboard.
**Validates: Requirements 8.5**

### Property 31: Loading Indicator Timing
*For any* chat message send action, a loading indicator should be displayed within 100ms of the send action.
**Validates: Requirements 9.1**

### Property 32: Message Render Performance
*For any* API response containing a message, the message should be rendered in the UI within 50ms of receiving the response.
**Validates: Requirements 9.2**

### Property 33: Progress Cache Management
*For any* fetch of onboarding progress, the result should be cached for 30 seconds; when a state transition occurs, the cache should be invalidated and fresh data fetched.
**Validates: Requirements 9.3, 9.4**

### Property 34: Typing Indicator Debouncing
*For any* sequence of typing events in the chat input, typing indicators should be debounced to avoid excessive updates.
**Validates: Requirements 9.5**

### Property 35: Empty Message Validation
*For any* message that is empty or contains only whitespace, the frontend should prevent the API request and display the validation message "Please enter a message".
**Validates: Requirements 10.1**

### Property 36: Secure Token Storage
*For any* authentication token received from the backend, the token should be stored using secure mechanisms (httpOnly cookies or secure localStorage with appropriate flags).
**Validates: Requirements 10.2**

### Property 37: Authentication Header Inclusion
*For any* API request to an authenticated endpoint, the request should include the JWT token in the Authorization header with the format "Bearer {token}".
**Validates: Requirements 10.3**

### Property 38: Unauthorized Error Handling
*For any* 401 error response, the frontend should clear all stored credentials and redirect to the login page.
**Validates: Requirements 10.4**

### Property 39: XSS Prevention
*For any* user-generated content received from the API, the content should be sanitized before rendering to prevent XSS attacks.
**Validates: Requirements 10.5**

## Error Handling

### Error Classification

The frontend must handle four categories of errors:

1. **Authentication Errors (401)**
   - Clear stored credentials
   - Redirect to login page
   - Preserve intended destination for post-login redirect

2. **Authorization Errors (403)**
   - ONBOARDING_REQUIRED: Redirect to /onboarding with progress info
   - AGENT_NOT_ALLOWED: Display error message in chat
   - Onboarding already complete: Redirect to main chat

3. **Client Errors (400)**
   - State mismatch: Fetch current state and resync
   - Validation errors: Display field-specific error messages
   - Invalid request: Display generic error with retry option

4. **Server Errors (500)**
   - Display user-friendly error message
   - Provide retry button
   - Log error details for debugging

### Error Recovery Strategies

```typescript
class ErrorHandler {
  handle(error: APIError): void {
    switch (error.status) {
      case 401:
        this.handleUnauthorized();
        break;
      case 403:
        this.handleForbidden(error.data);
        break;
      case 400:
        this.handleBadRequest(error.data);
        break;
      case 500:
        this.handleServerError();
        break;
      default:
        this.handleUnknownError(error);
    }
  }
  
  private handleUnauthorized(): void {
    // Clear auth state
    authStore.logout();
    // Redirect to login with return URL
    navigate('/login', { state: { from: location.pathname } });
  }
  
  private handleForbidden(data: ErrorResponse): void {
    if (data.error_code === 'ONBOARDING_REQUIRED') {
      // Show progress info and redirect
      toast.info(`Complete onboarding: ${data.onboarding_progress?.completion_percentage}% done`);
      navigate(data.redirect || '/onboarding');
    } else if (data.error_code === 'AGENT_NOT_ALLOWED') {
      // Show error in chat
      chatStore.addSystemMessage(data.message);
    }
  }
  
  private handleBadRequest(data: any): void {
    if (data.detail?.includes('State mismatch')) {
      // Resync state
      chatStore.addSystemMessage('Syncing your progress...');
      onboardingStore.fetchProgress();
    } else {
      // Show validation errors
      toast.error(data.detail || 'Invalid request');
    }
  }
  
  private handleServerError(): void {
    toast.error('Something went wrong. Please try again.', {
      action: {
        label: 'Retry',
        onClick: () => this.retry(),
      },
    });
  }
}
```

### Offline Handling

```typescript
class OfflineManager {
  private messageQueue: QueuedMessage[] = [];
  private isOnline: boolean = navigator.onLine;
  
  constructor() {
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }
  
  queueMessage(message: QueuedMessage): void {
    this.messageQueue.push(message);
    this.persistQueue();
  }
  
  private async handleOnline(): Promise<void> {
    this.isOnline = true;
    toast.success('Back online. Sending queued messages...');
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue[0];
      try {
        await this.sendMessage(message);
        this.messageQueue.shift();
        this.persistQueue();
      } catch (error) {
        // If send fails, stop processing queue
        toast.error('Failed to send queued messages');
        break;
      }
    }
  }
  
  private handleOffline(): void {
    this.isOnline = false;
    toast.warning('You are offline. Messages will be sent when connection is restored.');
  }
}
```

## Testing Strategy

### Testing Approach

The frontend implementation requires a dual testing approach combining unit tests and property-based tests:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
- Component rendering with specific props
- User interaction flows (click, type, submit)
- API error scenarios with specific error codes
- Edge cases (empty messages, invalid states)

**Property-Based Tests**: Verify universal properties across all inputs
- State management invariants
- Routing logic for all user states
- UI rendering for all valid state combinations
- Error handling for all error types

### Testing Framework

**Primary Framework**: Jest + React Testing Library
- `@testing-library/react`: Component testing with user-centric queries
- `@testing-library/user-event`: Realistic user interaction simulation
- `@testing-library/jest-dom`: Custom matchers for DOM assertions
- `msw` (Mock Service Worker): API mocking for integration tests
- `fast-check`: Property-based testing library for JavaScript/TypeScript

### Test Organization

```
frontend/src/
├── components/
│   ├── OnboardingGuard/
│   │   ├── OnboardingGuard.tsx
│   │   ├── OnboardingGuard.test.tsx
│   │   └── OnboardingGuard.properties.test.tsx
│   ├── ProgressIndicator/
│   │   ├── ProgressIndicator.tsx
│   │   ├── ProgressIndicator.test.tsx
│   │   └── ProgressIndicator.properties.test.tsx
│   └── ChatInterface/
│       ├── ChatInterface.tsx
│       ├── ChatInterface.test.tsx
│       └── ChatInterface.properties.test.tsx
├── hooks/
│   ├── useOnboarding.ts
│   ├── useOnboarding.test.ts
│   └── useOnboarding.properties.test.ts
└── services/
    ├── apiClient.ts
    ├── apiClient.test.ts
    └── apiClient.properties.test.ts
```

### Property-Based Test Configuration

Each property test must:
- Run minimum 100 iterations (due to randomization)
- Reference the design document property number
- Use appropriate generators for test data
- Tag format: `Feature: frontend-backend-api-alignment, Property {number}: {property_text}`

### Example Property Test

```typescript
import fc from 'fast-check';
import { render, screen } from '@testing-library/react';
import { NavigationMenu } from './NavigationMenu';

describe('Property 1: Navigation Lock State Consistency', () => {
  it('should disable all nav items when onboarding incomplete, enable when complete', () => {
    // Feature: frontend-backend-api-alignment, Property 1: Navigation Lock State Consistency
    
    fc.assert(
      fc.property(
        fc.record({
          id: fc.uuid(),
          email: fc.emailAddress(),
          onboarding_completed: fc.boolean(),
        }),
        (user) => {
          const { container } = render(
            <NavigationMenu user={user} />
          );
          
          const navButtons = container.querySelectorAll('.nav-item');
          
          navButtons.forEach((button) => {
            if (user.onboarding_completed) {
              expect(button).not.toBeDisabled();
              expect(button).not.toHaveClass('locked');
            } else {
              expect(button).toBeDisabled();
              expect(button).toHaveClass('locked');
            }
          });
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Example Unit Test

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from './ChatInterface';
import { server } from '../mocks/server';
import { rest } from 'msw';

describe('ChatInterface', () => {
  it('should display welcome message on first entry to onboarding', () => {
    render(
      <ChatInterface mode="onboarding" currentState={1} />
    );
    
    expect(screen.getByText(/welcome to shuren/i)).toBeInTheDocument();
    expect(screen.getByText(/let's get started/i)).toBeInTheDocument();
  });
  
  it('should handle state mismatch error and resync', async () => {
    const user = userEvent.setup();
    
    // Mock 400 error response
    server.use(
      rest.post('/api/v1/chat/onboarding', (req, res, ctx) => {
        return res(
          ctx.status(400),
          ctx.json({
            detail: 'State mismatch. Current: 3, Requested: 2'
          })
        );
      })
    );
    
    render(
      <ChatInterface mode="onboarding" currentState={2} />
    );
    
    const input = screen.getByPlaceholderText(/type your response/i);
    await user.type(input, 'My response');
    await user.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/syncing your progress/i)).toBeInTheDocument();
    });
  });
});
```

### Test Coverage Requirements

- **Unit Test Coverage**: 80%+ for all components and services
- **Property Test Coverage**: All 39 correctness properties must have corresponding property tests
- **Integration Test Coverage**: All critical user flows (login → onboarding → completion → chat)
- **Accessibility Test Coverage**: All interactive components tested with axe-core

### Continuous Integration

Tests should run automatically on:
- Pull requests to main branch
- Commits to feature branches
- Pre-deployment checks

Minimum requirements for passing:
- All unit tests pass
- All property tests pass (100 iterations each)
- Coverage >= 80%
- No accessibility violations
- No TypeScript errors

## Performance Considerations

### Optimization Strategies

1. **Code Splitting**
   - Lazy load onboarding components
   - Lazy load main app components
   - Separate vendor bundles

2. **State Management**
   - Use React Context for global state
   - Memoize expensive computations
   - Debounce user input events

3. **API Optimization**
   - Cache onboarding progress (30s TTL)
   - Batch multiple state updates
   - Use HTTP/2 multiplexing

4. **Rendering Optimization**
   - Virtual scrolling for long message lists
   - Memoize message components
   - Use CSS animations over JavaScript

### Performance Budgets

- Initial page load: < 2s
- Time to interactive: < 3s
- API response handling: < 50ms
- State update rendering: < 16ms (60fps)
- Bundle size: < 200KB (gzipped)

## Security Considerations

### Authentication Security

- Store JWT tokens in httpOnly cookies (preferred) or secure localStorage
- Implement token refresh mechanism
- Clear tokens on logout or 401 errors
- Use HTTPS for all API requests

### XSS Prevention

- Sanitize all user-generated content before rendering
- Use React's built-in XSS protection (JSX escaping)
- Implement Content Security Policy headers
- Validate and sanitize API responses

### CSRF Protection

- Include CSRF tokens in state-changing requests
- Validate origin headers
- Use SameSite cookie attribute

## Deployment Considerations

### Environment Configuration

```typescript
interface EnvironmentConfig {
  API_BASE_URL: string;
  AUTH_COOKIE_DOMAIN: string;
  ENABLE_ANALYTICS: boolean;
  LOG_LEVEL: 'debug' | 'info' | 'warn' | 'error';
}

const config: EnvironmentConfig = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  AUTH_COOKIE_DOMAIN: process.env.REACT_APP_AUTH_COOKIE_DOMAIN || 'localhost',
  ENABLE_ANALYTICS: process.env.REACT_APP_ENABLE_ANALYTICS === 'true',
  LOG_LEVEL: (process.env.REACT_APP_LOG_LEVEL as any) || 'info',
};
```

### Build Configuration

- Production build with minification
- Source maps for debugging
- Environment-specific configurations
- CDN for static assets

### Monitoring and Logging

- Log all API errors with context
- Track user flows through analytics
- Monitor performance metrics
- Alert on error rate thresholds

## Conclusion

This design provides a comprehensive frontend architecture that integrates seamlessly with the validated backend onboarding system. The implementation focuses on three core pillars:

1. **Robust State Management**: Tracking user authentication and onboarding status with proper synchronization
2. **Intelligent API Integration**: Correct endpoint routing, comprehensive error handling, and offline support
3. **Rich User Experience**: Navigation locks, progress indicators, responsive design, and accessibility

The design ensures that all users complete the mandatory 9-state onboarding flow before accessing application features, with clear visual feedback and error recovery throughout the journey.
