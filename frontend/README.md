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
│   │   ├── onboarding/        # Onboarding steps (12 steps)
│   │   ├── dashboard/         # Dashboard widgets
│   │   ├── chat/              # Text chat interface
│   │   ├── voice/             # Voice session interface (LiveKit)
│   │   ├── meals/             # Meal views
│   │   ├── workouts/          # Workout views
│   │   ├── common/            # Shared components
│   │   └── layout/            # Layout components
│   ├── contexts/              # React contexts (Auth, User, Voice)
│   ├── services/              # API services
│   ├── hooks/                 # Custom React hooks
│   ├── types/                 # TypeScript type definitions
│   ├── pages/                 # Page components
│   ├── App.tsx                # Main app component
│   └── main.tsx               # Entry point
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
- ✅ Onboarding (12-step flow)
- ✅ User profiles
- ✅ Meal management
- ✅ Workout management

### Phase 2 Backend
- ✅ Text chat with AI agents (6 specialized agents)
- ✅ LiveKit voice sessions
- ✅ Real-time transcription (Deepgram STT)
- ✅ Voice responses (Cartesia TTS)

## Development Guidelines

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

### Backend Connection Issues
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend
- Verify `VITE_API_BASE_URL` in `.env`

### Build Issues
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## Next Steps

This is Task 1 (Project Setup) complete. Next tasks:
1. Core infrastructure and API client
2. Authentication system
3. User profile and context
4. Onboarding flow
5. Dashboard page
6. Text chat interface
7. Voice session interface
8. Meal management
9. Workout management

See `.kiro/specs/minimal-frontend-testing/tasks.md` for full implementation plan.
