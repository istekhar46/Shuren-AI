# Minimal Frontend for Backend Testing - Requirements

## 1. Overview

Create a minimal React-based web frontend to test the Shuren AI backend (Phase 1 & 2 complete). This is a testing interface, not the final production app. The goal is to validate all backend endpoints, AI agent functionality, and LiveKit voice integration.

**Backend Status:**
- ✅ Phase 1: FastAPI, PostgreSQL, Auth, Onboarding, Profiles, Meals, Workouts
- ✅ Phase 2: LangChain agents (6 specialized), Text chat API, LiveKit voice infrastructure
- ⏳ Phase 3: Celery schedulers and background tasks (pending)

This frontend will test both text chat and voice interactions with the AI agents.

## 2. User Stories

### 2.1 Authentication & Account Creation
**As a tester**, I want to create an account and log in so that I can test the backend authentication system.

**Acceptance Criteria:**
- 2.1.1 User can register with email and password
- 2.1.2 User can log in with credentials
- 2.1.3 JWT token is stored and used for authenticated requests
- 2.1.4 User can log out
- 2.1.5 Protected routes redirect to login if not authenticated

### 2.2 Onboarding Flow
**As a tester**, I want to complete the onboarding process so that I can test the multi-step onboarding backend.

**Acceptance Criteria:**
- 2.2.1 Display all 12 onboarding steps in sequence
- 2.2.2 Each step saves data to backend via API
- 2.2.3 User can navigate back to previous steps
- 2.2.4 Progress indicator shows current step
- 2.2.5 Final step locks the profile and redirects to dashboard
- 2.2.6 Validation errors from backend are displayed clearly

### 2.3 Dashboard & Profile View
**As a tester**, I want to view my profile and current plans so that I can verify data persistence.

**Acceptance Criteria:**
- 2.3.1 Dashboard displays user's fitness level, goals, and energy level
- 2.3.2 Meal plan summary is visible (calories, macros, meal count)
- 2.3.3 Workout schedule is displayed (days, time, duration)
- 2.3.4 User can view full profile details
- 2.3.5 User can unlock and edit profile (with confirmation)

### 2.4 Text Chat with AI Agents
**As a tester**, I want to chat with AI agents so that I can test agent orchestration and responses.

**Acceptance Criteria:**
- 2.4.1 Chat interface with message history
- 2.4.2 User can send text messages to agents
- 2.4.3 Agent responses are displayed in real-time
- 2.4.4 User can select specific agent type (workout, diet, supplement, tracker, scheduler, general)
- 2.4.5 Chat history persists during session
- 2.4.6 Loading indicator while waiting for agent response
- 2.4.7 Error messages displayed if agent fails

### 2.5 Meal Management
**As a tester**, I want to view and manage meals so that I can test meal-related endpoints.

**Acceptance Criteria:**
- 2.5.1 View meal plan with all scheduled meals
- 2.5.2 View meal details (ingredients, macros, instructions)
- 2.5.3 Search and browse available dishes
- 2.5.4 Request meal substitutions via chat
- 2.5.5 Generate shopping list for upcoming meals
- 2.5.6 View shopping list with ingredients grouped by category

### 2.6 Workout Management
**As a tester**, I want to view and log workouts so that I can test workout-related endpoints.

**Acceptance Criteria:**
- 2.6.1 View current workout schedule
- 2.6.2 View today's workout details (exercises, sets, reps)
- 2.6.3 Log completed sets with weight and reps
- 2.6.4 Mark workout as complete
- 2.6.5 View workout history
- 2.6.6 Request exercise demonstrations via chat

### 2.7 Voice Session Testing
**As a tester**, I want to test voice interactions with AI agents so that I can validate LiveKit integration.

**Acceptance Criteria:**
- 2.7.1 Button to start voice session with agent type selection
- 2.7.2 LiveKit room connection established via backend API
- 2.7.3 Microphone access requested and granted
- 2.7.4 Voice activity indicator shows when speaking
- 2.7.5 Real-time transcription displayed (from Deepgram STT)
- 2.7.6 Agent voice responses play through speakers (Cartesia TTS)
- 2.7.7 Session status shows connection state and participant count
- 2.7.8 End voice session button terminates connection
- 2.7.9 Error handling for connection failures
- 2.7.10 Latency indicator shows response time

## 3. Technical Requirements

### 3.1 Technology Stack
- **Framework:** React (latest) with TypeScript
- **Build Tool:** Vite (latest)
- **Routing:** React Router (latest)
- **State Management:** React Context API + hooks (no Redux needed for MVP)
- **HTTP Client:** Axios (latest)
- **UI Components:** Shadcn/ui (Tailwind CSS based, latest)
- **Voice (Phase 3):** LiveKit React SDK (@livekit/components-react, latest)

### 3.2 Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/              # Login, Register
│   │   ├── onboarding/        # Onboarding steps (12 steps)
│   │   ├── dashboard/         # Dashboard widgets
│   │   ├── chat/              # Text chat interface
│   │   ├── voice/             # Voice session interface (LiveKit)
│   │   ├── meals/             # Meal views
│   │   ├── workouts/          # Workout views
│   │   └── common/            # Shared components
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   ├── UserContext.tsx
│   │   └── VoiceContext.tsx   # Voice session state
│   ├── services/
│   │   ├── api.ts             # Axios instance
│   │   ├── authService.ts
│   │   ├── onboardingService.ts
│   │   ├── chatService.ts
│   │   ├── voiceService.ts    # LiveKit integration
│   │   ├── mealService.ts
│   │   └── workoutService.ts
│   ├── hooks/
│   │   ├── useVoiceSession.ts # LiveKit room management
│   │   └── useChat.ts         # Chat state management
│   ├── types/
│   │   └── index.ts           # TypeScript interfaces
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── OnboardingPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── VoicePage.tsx      # Voice session page
│   │   ├── MealsPage.tsx
│   │   └── WorkoutsPage.tsx
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 3.3 API Integration
- Base URL: `http://localhost:8000/api/v1`
- JWT token stored in localStorage
- Axios interceptor for automatic token injection
- Error handling for 401 (redirect to login), 422 (validation errors), 500 (server errors)

**Key Backend Endpoints:**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /onboarding/step` - Save onboarding step
- `GET /profiles/me` - Get user profile
- `POST /chat/chat` - Send text message to agent
- `POST /chat/stream` - Streaming chat (SSE)
- `GET /chat/history` - Get conversation history
- `POST /voice-sessions/start` - Create LiveKit voice session
- `GET /voice-sessions/{room_name}/status` - Get session status
- `DELETE /voice-sessions/{room_name}` - End voice session
- `GET /meals/plan` - Get meal plan
- `GET /workouts/schedule` - Get workout schedule

### 3.4 Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Touch-friendly buttons and inputs
- Readable font sizes on all devices

### 3.5 Performance
- Code splitting by route
- Lazy loading for non-critical components
- Debounced search inputs
- Optimistic UI updates where appropriate

## 4. Non-Functional Requirements

### 4.1 Usability
- Clear error messages
- Loading states for all async operations
- Confirmation dialogs for destructive actions
- Keyboard navigation support

### 4.2 Accessibility
- Semantic HTML
- ARIA labels where needed
- Keyboard accessible
- Color contrast meets WCAG AA standards

### 4.3 Browser Support
- Latest versions of Chrome, Firefox, Safari, and Edge
- Modern browsers with ES6+ support

### 4.4 Development Experience
- TypeScript for type safety
- ESLint for code quality
- Prettier for code formatting
- Hot module replacement during development

## 5. Out of Scope (MVP)

- ❌ Mobile native apps (iOS/Android)
- ❌ Offline support
- ❌ Push notifications
- ❌ Social features
- ❌ Advanced analytics dashboard
- ❌ Wearable integrations
- ❌ Payment processing
- ❌ Admin panel
- ❌ Multi-language support
- ❌ Dark mode (can be added later)

## 6. Success Criteria

The minimal frontend is successful if:
1. All Phase 1 & 2 backend endpoints can be tested
2. Onboarding flow completes successfully
3. AI agents respond correctly to text queries
4. Meal and workout data displays accurately
5. Authentication works end-to-end
6. No critical bugs in core user flows
7. Codebase is clean and maintainable for future expansion

## 7. Future Enhancements (Post-MVP)

After validating backend functionality:
1. Enhance voice UI with waveform visualization
2. Add real-time notifications for reminders (Phase 3)
3. Enhance UI/UX with animations and transitions
4. Add progress tracking visualizations and charts
5. Implement mobile-responsive improvements
6. Add workout GIF demonstrations in workout view
7. Implement meal photo uploads
8. Add conversation export functionality
9. Implement voice session recording/playback
10. Add agent performance metrics dashboard

## 8. Dependencies

### Backend Requirements
- Backend server running on `http://localhost:8000`
- PostgreSQL database populated with seed data (dishes, exercises)
- All Phase 1 & 2 endpoints functional:
  - Auth endpoints (register, login)
  - Onboarding endpoints (12 steps)
  - Profile endpoints
  - Chat endpoints (text + streaming)
  - Voice session endpoints (LiveKit)
  - Meal and workout endpoints
- LiveKit server accessible (cloud or self-hosted)
- LangChain agents operational (6 specialized agents)

### External Services
- LiveKit server (for voice sessions)
- Deepgram API (STT - handled by backend)
- Cartesia API (TTS - handled by backend)
- Anthropic/OpenAI API (LLM - handled by backend)

## 9. Timeline Estimate

- **Setup & Auth:** 1 day
- **Onboarding Flow:** 2 days (12 steps)
- **Dashboard & Profile:** 1 day
- **Text Chat Interface:** 2 days (including streaming)
- **Voice Session Interface:** 2 days (LiveKit integration)
- **Meals Management:** 1 day
- **Workouts Management:** 1 day
- **Testing & Bug Fixes:** 2 days

**Total:** ~12 days for a single developer

## 10. Testing Strategy

### Manual Testing
- Test all user flows end-to-end
- Test on different browsers
- Test on different screen sizes
- Test error scenarios (network failures, validation errors)

### Automated Testing (Optional for MVP)
- Unit tests for utility functions
- Integration tests for API services
- E2E tests for critical flows (login, onboarding)

## 11. Deployment

### Development
- Run locally with `npm run dev`
- Connect to local backend

### Staging (Optional)
- Deploy to Vercel/Netlify
- Connect to staging backend
- Use for demo purposes

### Production
- Not needed for MVP (testing tool only)
- Can be deployed later for beta users
