# Shuren AI - Frontend Testing Interface

Minimal React-based web frontend to test the Shuren AI backend (Phase 1 & 2). This is a testing interface, not the final production app.

## Technology Stack

- **Framework:** React 19 with TypeScript
- **Build Tool:** Vite 7
- **Routing:** React Router 7
- **State Management:** React Context API + hooks
- **HTTP Client:** Axios
- **Styling:** Tailwind CSS 4
- **Code Quality:** ESLint + Prettier

## Prerequisites

- Node.js 18+ and npm
- Backend server running on `http://localhost:8000`

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_LIVEKIT_URL=ws://localhost:7880
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors automatically
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/              # Login, Register
│   │   ├── onboarding/        # Agent-based onboarding components
│   │   │   ├── AgentHeader.tsx           # Current agent display
│   │   │   ├── OnboardingProgressBar.tsx # 9-state progress tracker
│   │   │   ├── PlanPreviewCard.tsx       # Plan approval UI
│   │   │   ├── WorkoutPlanPreview.tsx    # Workout plan display
│   │   │   └── MealPlanPreview.tsx       # Meal plan display
│   │   ├── dashboard/         # Dashboard widgets
│   │   ├── chat/              # Text chat interface
│   │   ├── voice/             # Voice session interface (LiveKit)
│   │   ├── meals/             # Meal views
│   │   ├── workouts/          # Workout views
│   │   ├── common/            # Shared components
│   │   └── layout/            # Layout components
│   ├── contexts/              # React contexts (Auth, User, Voice)
│   ├── services/              # API services
│   │   ├── api.ts                        # Base API client
│   │   ├── authService.ts                # Authentication
│   │   ├── onboardingService.ts          # Onboarding API
│   │   └── planDetectionService.ts       # Plan parsing
│   ├── hooks/                 # Custom React hooks
│   │   └── useOnboardingChat.ts          # Onboarding state management
│   ├── types/                 # TypeScript type definitions
│   │   └── onboarding.types.ts           # Onboarding types
│   ├── pages/                 # Page components
│   │   ├── OnboardingChatPage.tsx        # Main onboarding UI
│   │   └── ...
│   ├── App.tsx                # Main app component
│   └── main.tsx               # Entry point
├── tests/                     # Test files
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── properties/            # Property-based tests
│   └── e2e/                   # End-to-end tests
│       ├── complete-onboarding.e2e.test.tsx
│       ├── approve-workout-plan.e2e.test.tsx
│       ├── request-meal-plan-changes.e2e.test.tsx
│       └── complete-onboarding-redirect.e2e.test.tsx
├── public/                    # Static assets
├── .env                       # Environment variables (not committed)
├── .env.example               # Environment variables template
├── tailwind.config.js         # Tailwind CSS configuration
├── vite.config.ts             # Vite configuration
└── package.json               # Dependencies and scripts
```

## Features to Test

### Phase 1 Backend
- ✅ Authentication (register, login, JWT)
- ✅ User profiles
- ✅ Meal management
- ✅ Workout management

### Phase 2 Backend
- ✅ Text chat with AI agents (6 specialized agents)
- ✅ LiveKit voice sessions
- ✅ Real-time transcription (Deepgram STT)
- ✅ Voice responses (Cartesia TTS)

### Agent-Based Onboarding (Latest)
- ✅ Conversational onboarding with 5 specialized AI agents
- ✅ 9-state onboarding flow (replacing old 12-step form)
- ✅ Real-time streaming responses
- ✅ Workout plan generation and approval
- ✅ Meal plan generation and approval
- ✅ Progress tracking with visual indicators
- ✅ Agent context display (current agent, state, description)

## Development Guidelines

### Agent-Based Onboarding Flow

The new onboarding system uses conversational AI agents instead of traditional forms:

#### Architecture
- **5 Specialized Agents**: Fitness Assessment, Goal Setting, Workout Planning, Diet Planning, Scheduling
- **9 States**: User progresses through 9 onboarding states (0-8)
- **Streaming Responses**: Real-time SSE streaming for natural conversation
- **Plan Approval**: Interactive review and approval of workout/meal plans

#### Key Components
- `OnboardingChatPage`: Main container with chat interface
- `AgentHeader`: Displays current agent and state information
- `OnboardingProgressBar`: Visual progress through 9 states
- `PlanPreviewCard`: Modal for reviewing workout/meal plans
- `useOnboardingChat`: Custom hook managing onboarding state

#### API Endpoints
- `GET /api/v1/onboarding/progress` - Get current onboarding state
- `GET /api/v1/chat/onboarding-stream` - Stream chat responses (SSE)
- `POST /api/v1/onboarding/complete` - Complete onboarding and create profile

#### State Flow
1. **State 0**: Fitness Level Assessment
2. **State 1**: Primary Fitness Goals
3. **State 2**: Workout Preferences & Constraints
4. **State 3**: Dietary Preferences & Restrictions
5. **State 4**: Meal Planning Preferences
6. **State 5**: Workout Schedule & Timing
7. **State 6**: Lifestyle & Baseline Assessment
8. **State 7**: Workout Plan Generation & Approval
9. **State 8**: Meal Plan Generation & Approval

#### Testing
- Unit tests for components and hooks
- Property-based tests for state consistency
- Integration tests for complete flows
- E2E tests for user journeys

Run tests:
```bash
npm test                           # Run all tests
npm test tests/unit/              # Unit tests only
npm test tests/e2e/               # E2E tests only
npm test -- --coverage            # With coverage report
```

### Code Style
- Use TypeScript for type safety
- Follow React hooks patterns
- Use Tailwind CSS for styling
- Keep components small and focused
- Use async/await for API calls

### API Integration
- All API calls go through `src/services/api.ts`
- JWT token automatically injected via interceptor
- 401 errors redirect to login automatically

### State Management
- Use React Context for global state (Auth, User, Voice)
- Use local state for component-specific data
- Keep state minimal and focused

## Troubleshooting

### Onboarding Issues
- **Streaming not working**: Check SSE connection, verify backend is running
- **State not updating**: Refresh progress from `/onboarding/progress` endpoint
- **Plans not displaying**: Check plan detection logic in `planDetectionService`
- **Can't complete onboarding**: Ensure all 9 states are completed (100% progress)

### Backend Connection Issues
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend
- Verify `VITE_API_BASE_URL` in `.env`

### Build Issues
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## Next Steps

This frontend implements the agent-based onboarding system integrated with the Shuren AI backend.

### Completed Features
1. ✅ Project setup and infrastructure
2. ✅ Authentication system
3. ✅ User profile and context
4. ✅ Agent-based onboarding flow (9 states)
5. ✅ Dashboard page
6. ✅ Text chat interface
7. ✅ Voice session interface
8. ✅ Meal management
9. ✅ Workout management

### Future Enhancements
- Voice-based onboarding
- Inline plan editing
- Multi-language support
- Enhanced accessibility features
- Offline mode with progress caching

See `.kiro/specs/frontend-onboarding-agent-integration/` for detailed implementation documentation.
