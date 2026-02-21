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
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

#### Google OAuth Setup

To enable "Sign in with Google" functionality:

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note your project ID

2. **Enable Google Identity Services**
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "Google Identity Services"
   - Click "Enable"

3. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - If prompted, configure the OAuth consent screen:
     - User Type: External (for testing) or Internal (for organization)
     - App name: Shuren AI
     - User support email: Your email
     - Developer contact: Your email
   - Application type: "Web application"
   - Name: "Shuren Frontend"

4. **Configure Authorized Origins** ⚠️ CRITICAL STEP
   - In the OAuth 2.0 Client ID settings, find "Authorized JavaScript origins"
   - Click "ADD URI" and add these origins:
     - `http://localhost:3000` (if using port 3000)
     - `http://localhost:5173` (Vite default port)
     - Add your production domain when deploying (e.g., `https://yourdomain.com`)
   - **Important**: The origin must match EXACTLY where your frontend is running
   - Authorized redirect URIs are not needed for Google Identity Services
   - Click "Save" at the bottom of the page
   
   **Common Error**: If you see "The given origin is not allowed for the given client ID":
   - This means the origin is not added to authorized JavaScript origins
   - Check which port your frontend is running on (look at the browser URL)
   - Add that exact origin (including `http://` and port number)
   - Wait 1-2 minutes for Google's changes to propagate
   - Clear browser cache and reload the page

5. **Copy Client ID**
   - Copy the generated Client ID (format: `xxxxx.apps.googleusercontent.com`)
   - Paste it in your `.env` file as `VITE_GOOGLE_CLIENT_ID`

6. **Testing**
   - The Google OAuth button will appear on login and registration pages
   - Test with your Google account
   - For production, submit your app for OAuth verification

**Note**: The Client ID is public and safe to include in frontend code. The backend validates the Google ID token for security.

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
│   │   │   ├── OnboardingProgressBar.tsx # 4-step progress tracker
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
- ✅ Conversational onboarding with 4 specialized AI agents
- ✅ 4-step onboarding flow (replacing old 12-step form)
- ✅ Real-time streaming responses
- ✅ Workout plan generation and approval
- ✅ Meal plan generation and approval
- ✅ Progress tracking with visual indicators
- ✅ Agent context display (current agent, step, description)

## Development Guidelines

### Agent-Based Onboarding Flow

The new onboarding system uses conversational AI agents instead of traditional forms:

#### Architecture
- **4 Specialized Agents**: Fitness Assessment, Workout Planning, Diet Planning, Scheduling
- **4 Steps**: User progresses through 4 onboarding steps (1-4)
- **Streaming Responses**: Real-time SSE streaming for natural conversation
- **Plan Approval**: Interactive review and approval of workout/meal plans

#### Key Components
- `OnboardingChatPage`: Main container with chat interface
- `AgentHeader`: Displays current agent and step information
- `OnboardingProgressBar`: Visual progress through 4 steps
- `PlanPreviewCard`: Modal for reviewing workout/meal plans
- `useOnboardingChat`: Custom hook managing onboarding state

#### API Endpoints
- `GET /api/v1/onboarding/progress` - Get current onboarding state
- `GET /api/v1/chat/onboarding-stream` - Stream chat responses (SSE)
- `POST /api/v1/onboarding/complete` - Complete onboarding and create profile

#### Step Flow
1. **Step 1**: Fitness Assessment (fitness level, experience, goals)
2. **Step 2**: Workout Planning (equipment, schedule, constraints)
3. **Step 3**: Diet Planning (diet type, allergies, meal preferences)
4. **Step 4**: Scheduling (hydration, supplements, reminders)

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
- **Step not updating**: Refresh progress from `/onboarding/progress` endpoint
- **Plans not displaying**: Check plan detection logic in `planDetectionService`
- **Can't complete onboarding**: Ensure all 4 steps are completed (100% progress)

### Google OAuth Issues

**Error: "The given origin is not allowed for the given client ID"**
- **Cause**: Your frontend URL is not added to "Authorized JavaScript origins" in Google Cloud Console
- **Solution**:
  1. Check which port your frontend is running on (e.g., `http://localhost:3000` or `http://localhost:5173`)
  2. Go to [Google Cloud Console](https://console.cloud.google.com/) > APIs & Services > Credentials
  3. Click on your OAuth 2.0 Client ID
  4. Under "Authorized JavaScript origins", click "ADD URI"
  5. Add the exact URL where your frontend is running (e.g., `http://localhost:3000`)
  6. Click "Save"
  7. Wait 1-2 minutes for changes to propagate
  8. Clear browser cache and reload the page

**Error: "CSRF token not found"**
- **Cause**: Google Identity Services didn't set the g_csrf_token cookie (expected for button flow)
- **Solution**: This is normal for the button flow. The frontend sends an empty string for CSRF token, which the backend accepts.

**Error: "Token has wrong audience"**
- **Cause**: Backend is configured with a different Google Client ID than the frontend
- **Solution**: 
  1. Check `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`
  2. Check `GOOGLE_CLIENT_ID` in `backend/.env`
  3. Both must be the SAME Client ID from Google Cloud Console
  4. Restart both frontend and backend after changing

**Google button not appearing**
- **Cause**: Script loading timing issue or configuration error
- **Solution**:
  1. Check browser console for errors
  2. Verify `VITE_GOOGLE_CLIENT_ID` is set in `.env`
  3. Clear browser cache and reload
  4. Check that Google Identity Services script loaded (look for console log)
  5. Try navigating to a different page and back

**Third-party cookies warning**
- **Cause**: Chrome is phasing out third-party cookies
- **Impact**: This warning is informational and doesn't affect functionality
- **Solution**: No action needed. Google Identity Services works without third-party cookies.

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
4. ✅ Agent-based onboarding flow (4 steps)
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
