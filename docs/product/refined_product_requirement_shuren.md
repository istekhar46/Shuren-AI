# Refined Product Requirements - Shuren AI

---

## 1. Overview

This document defines the refined user journey and functional requirements for the Shuren AI fitness application, focusing on the onboarding-first approach and agent-based interaction model.

---

## 2. Core User Flow

### 2.1 Registration
- User registers on the platform using email/password or OAuth
- Upon successful registration, user is immediately directed to onboarding

### 2.2 Onboarding Lock
- **All navigation is locked until onboarding is complete**
- User sees clear instructions: "Complete onboarding to unlock full access"
- Only the chat interface is accessible during onboarding
- No access to dashboard, profile, or other features until onboarding completes

### 2.3 Onboarding via Chat Interface
- User enters the chat section to begin onboarding
- A welcome message greets the user and explains the onboarding process
- Each onboarding state presents:
  - Clear question(s) relevant to that state
  - Context about why this information is needed
  - Visual indicators of current progress

---

## 3. Onboarding States & Agent Mapping

Each onboarding state is handled by a specialized agent that collects information and updates the user profile via API endpoints.

### Onboarding States (Reference: RFP.md)

1. **Fitness Level Assessment**
   - Agent: Workout Planning Agent
   - Collects: Beginner / Intermediate / Advanced
   - Endpoint: `POST /api/v1/onboarding/fitness-level`

2. **Primary Fitness Goals**
   - Agent: Workout Planning Agent
   - Collects: Fat loss / Muscle gain / General fitness
   - Endpoint: `POST /api/v1/onboarding/goals`

3. **Workout Preferences & Constraints**
   - Agent: Workout Planning Agent
   - Collects: Available equipment, injuries, limitations, preferred workout types
   - Endpoint: `POST /api/v1/onboarding/workout-preferences`

4. **Diet Preferences & Restrictions**
   - Agent: Diet Planning Agent
   - Collects: Diet type (vegetarian, vegan, etc.), allergies, food restrictions
   - Endpoint: `POST /api/v1/onboarding/diet-preferences`

5. **Fixed Meal Plan Selection**
   - Agent: Diet Planning Agent
   - Collects: Meal structure, calorie targets, protein targets
   - Endpoint: `POST /api/v1/onboarding/meal-plan`

6. **Meal Timing Schedule**
   - Agent: Scheduling & Reminder Agent
   - Collects: Breakfast, lunch, dinner, snack times
   - Endpoint: `POST /api/v1/onboarding/meal-schedule`

7. **Workout Schedule**
   - Agent: Scheduling & Reminder Agent
   - Collects: Workout days, preferred times
   - Endpoint: `POST /api/v1/onboarding/workout-schedule`

8. **Hydration Schedule**
   - Agent: Scheduling & Reminder Agent
   - Collects: Water intake goals, reminder frequency
   - Endpoint: `POST /api/v1/onboarding/hydration-schedule`

9. **Supplement Preferences (Optional)**
   - Agent: Supplement Guidance Agent
   - Collects: Interest in supplements, current usage
   - Endpoint: `POST /api/v1/onboarding/supplement-preferences`

---

## 4. Agent Behavior During Onboarding

### 4.1 Specialized Agents (Onboarding Only)
- **Workout Planning Agent**: Handles fitness level, goals, workout preferences
- **Diet Planning Agent**: Handles diet preferences, meal plans
- **Scheduling & Reminder Agent**: Handles all timing schedules
- **Supplement Guidance Agent**: Handles supplement preferences

### 4.2 Agent Tool Access
Each specialized agent has access to:
- **Function tools**: API endpoints to save onboarding data
- **User context**: Previously collected onboarding data
- **Validation logic**: Ensures data completeness before moving to next state

### 4.3 State Progression
- Agent asks relevant questions for current state
- User responds via chat (text input)
- Agent validates response
- Agent calls appropriate endpoint to save data
- Agent confirms completion and moves to next state
- UI updates to reflect progress

---

## 5. UI/UX Requirements During Onboarding

### 5.1 Progress Indicators
- Visual progress bar showing: "Step X of Y"
- List of completed states (checkmarks)
- Current state highlighted
- Upcoming states visible but grayed out

### 5.2 Chat Interface
- Welcome message on first entry
- Clear question for current state
- Conversational, friendly tone
- Validation feedback (e.g., "Great! I've saved your fitness level.")
- Smooth transition messages between states

### 5.3 Navigation Lock
- Sidebar/menu items disabled during onboarding
- Tooltip on hover: "Complete onboarding to unlock"
- No way to skip or bypass onboarding

---

## 6. Post-Onboarding Experience

### 6.1 Profile Completion
Once all onboarding states are complete:
- User profile is fully populated with:
  - Workout plan
  - Meal plan
  - Supplement preferences
  - All schedules (workout, meal, hydration)
  - Reminder settings
- Navigation unlocks
- User gains access to full application

### 6.2 General Agent Access
After onboarding:
- **Only the General Conversational Assistant Agent is available**
- Specialized agents are no longer directly accessible
- General Agent has access to:
  - Complete user profile
  - All user data (workouts, meals, schedules)
  - Relevant tools to query and display information

### 6.3 General Agent Capabilities
The General Agent can:
- Answer questions about user's workout plan
- Provide meal information and cooking guidance
- Show upcoming schedules
- Display workout demonstrations (GIFs)
- Offer motivational support
- Handle casual fitness-related conversations

**Example Queries:**
- "What's my workout today?"
- "Show me my meal plan for this week"
- "When is my next meal reminder?"
- "How do I perform a squat?"
- "I'm feeling tired, should I still work out?"

### 6.4 Tool Access for General Agent
The General Agent uses function tools to:
- `GET /api/v1/users/me/profile` - Fetch user profile
- `GET /api/v1/users/me/workouts` - Get workout plans
- `GET /api/v1/users/me/meals` - Get meal plans
- `GET /api/v1/users/me/schedules` - Get all schedules
- `GET /api/v1/exercises/{exercise_id}/demo` - Fetch exercise GIFs
- `POST /api/v1/tracking/log` - Log user activities

---

## 7. Key Functional Requirements

### 7.1 Onboarding
- ✅ Mandatory, cannot be skipped
- ✅ Sequential state progression
- ✅ Each state handled by specialized agent
- ✅ Real-time data persistence via API endpoints
- ✅ Clear UI progress indicators
- ✅ Navigation locked until completion

### 7.2 Agent Architecture
- ✅ Specialized agents active only during onboarding
- ✅ General agent active post-onboarding
- ✅ Agents use function tools to interact with backend
- ✅ All agents have access to user context

### 7.3 Chat Interface
- ✅ Primary interaction method during onboarding
- ✅ Conversational, natural language processing
- ✅ Text-based (voice optional for future)
- ✅ Context-aware responses

### 7.4 Data Persistence
- ✅ All onboarding data saved to user profile
- ✅ Profile serves as single source of truth
- ✅ Data accessible to General Agent post-onboarding
- ✅ Profile modifiable only through explicit user requests

---

## 8. Technical Boundaries

### 8.1 Agent Scope
- Specialized agents: Onboarding only
- General agent: Post-onboarding only
- No agent switching or selection by user
- System automatically routes to appropriate agent

### 8.2 Data Flow
```
User Input → Chat Interface → Active Agent → Function Tool (API Endpoint) → Database → User Profile
```

### 8.3 Context Management
- User profile loaded into agent context
- Previous onboarding responses available to subsequent agents
- General agent has full profile context

---

## 9. Success Criteria

### 9.1 Onboarding Completion
- User completes all 8-9 onboarding states
- All required data saved to profile
- Navigation unlocks automatically
- User can access full application

### 9.2 Post-Onboarding Usage
- User can ask fitness-related questions
- General agent provides accurate, context-aware responses
- User data (workouts, meals, schedules) accessible via chat
- No need for manual navigation to view plans

---

## 10. Out of Scope (MVP)

- Voice-based onboarding (text only)
- Mid-onboarding pause/resume (must complete in one session)
- Onboarding data editing (profile changes post-onboarding only)
- Multi-language support
- Advanced analytics during onboarding

---

## 11. Future Enhancements

- Voice-based onboarding option
- Ability to pause and resume onboarding
- Onboarding progress saved across sessions
- Re-onboarding flow for profile reset
- Visual onboarding summary at completion

---

## 12. Conclusion

This refined requirement establishes a clear, linear onboarding flow where:
1. User registers
2. Completes mandatory onboarding via chat with specialized agents
3. Agents save data to profile via API endpoints
4. Navigation unlocks upon completion
5. General agent provides ongoing assistance with full profile context

This approach ensures complete profile setup before user accesses the application, creating a solid foundation for personalized fitness guidance.
