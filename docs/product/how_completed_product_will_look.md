## **Complete User Journey**

### **Day 1: Onboarding & Setup**

**1. User Downloads App**
- Opens app, sees splash screen
- Taps "Get Started"

**2. Account Creation**
- User signs up with email/Google/Apple
- FastAPI receives auth request → creates User record in PostgreSQL
- `external_auth_id` stored, JWT token generated
- User redirected to onboarding flow

**3. Interactive Onboarding (Voice or Text)**
- User chooses: "Talk to AI Coach" or "Fill out form"

**If Voice Selected:**
```
User taps "Start Voice Onboarding"
    ↓
App calls: POST /api/v1/chat/start-voice-session
    ↓
FastAPI creates LiveKit room with metadata:
    - user_id
    - agent_type: "onboarding"
    - mode: "voice"
    ↓
Returns: room_name, access token, livekit_url
    ↓
App connects to LiveKit room using WebRTC
    ↓
LiveKit Agent Worker spins up FitnessVoiceAgent
    ↓
AI Coach speaks: "Hey! I'm your fitness coach. Let's get to know you. 
What's your main fitness goal?"
    ↓
User speaks: "I want to build muscle and lose some belly fat"
    ↓
Deepgram STT → converts speech to text
    ↓
Claude LLM processes with context → generates response
    ↓
Cartesia TTS → converts to natural voice
    ↓
AI: "Great! Building muscle while losing fat. How would you rate 
your current fitness level - beginner, intermediate, or advanced?"
```

The conversation continues through:
- Fitness level
- Experience with weights
- Workout frequency preference
- Dietary restrictions
- Meal prep willingness
- Energy levels throughout day
- Sleep patterns
- Injury history

**Behind the scenes:**
- Each answer stored in `OnboardingState` table
- Agent uses `@llm_function` to call `save_onboarding_answer()`
- PostgreSQL updates in real-time
- Redis caches partial progress

**If Text Selected:**
- Similar flow but through chat interface
- LiveKit TextAgent handles messages
- Same database updates

**4. Profile Generation**
- When onboarding completes, Celery task triggers:
```python
@celery_app.task
async def generate_initial_plans(user_id):
    # WorkoutPlannerAgent creates 12-week workout plan
    # DietPlannerAgent creates meal plan
    # SupplementGuideAgent recommends stack
    # All stored in PostgreSQL
```

- User sees: "Creating your personalized plan... ⏳"
- 30 seconds later: "Your plan is ready! 🎉"

---

### **Day 1 Evening: First Workout**

**5:30 PM - Scheduled Workout Time**

**Push Notification:**
```
Celery Beat runs send_workout_reminders every 15 minutes
    ↓
Finds user has workout scheduled at 5:30 PM
    ↓
Sends FCM push: "Leg Day! Ready to crush it? 💪"
```

**User Opens App:**
- Sees today's workout:
  - Squats: 4 sets x 8 reps
  - Romanian Deadlifts: 3 sets x 10 reps
  - Leg Press: 3 sets x 12 reps
  - Leg Curls: 3 sets x 15 reps

**User Taps "Start Workout with Voice Coach"**
```
POST /api/v1/chat/start-voice-session?agent_type=workout
    ↓
LiveKit room created
    ↓
WorkoutPlannerAgent loads:
    - User's current workout plan from PostgreSQL
    - Today's specific exercises
    - User's energy level (from profile)
    - Previous workout performance
    ↓
AI Coach: "Alright! Let's crush this leg day. We're starting with 
squats - 4 sets of 8 reps. Got your weight loaded?"
```

**During Workout:**
```
User: "Starting first set"
AI: "Perfect form! Remember - chest up, knees tracking over toes. 
Let me know when you finish."

[30 seconds later]
User: "Done, 8 reps with 185 pounds"
    ↓
Agent calls @llm_function log_set_completion(exercise="Squat", reps=8, weight=185)
    ↓
WorkoutLog inserted into PostgreSQL
    ↓
AI: "Solid! Rest 90 seconds. How's the energy level?"

User: "Feeling good"
AI: "Awesome. Ready for set 2 when you are."
```

**Mid-Workout Adjustment:**
```
User: "This weight feels too heavy today"
AI: [Checks user's energy_level="moderate" from profile]
"No problem! You mentioned moderate energy today. Let's drop to 
175 pounds. We're training for the long game."
    ↓
Agent updates WorkoutLog with modified weight
    ↓
AdaptivePlanningEngine (Celery task tonight) will note this
```

**Workout Completion:**
```
User: "Just finished leg curls!"
AI: "That's it! Leg day complete - crushed it! 🔥 
Great work pushing through. Don't forget to stretch."
    ↓
Agent marks workout as completed in database
    ↓
Progress tracking updated
    ↓
Achievement unlocked: "First Workout Complete" badge
```

---

### **Day 1, 7:00 PM - Dinner Time**

**Push Notification:**
```
Celery Beat: send_meal_reminders runs every 30 min
    ↓
User has dinner scheduled 7:00-7:30 PM
    ↓
FCM push: "Dinner time! Check your meal plan 🍽️"
```

**User Opens Meal Plan:**
- Sees: Grilled Chicken with Sweet Potato & Broccoli
  - 8oz chicken breast
  - 1 medium sweet potato
  - 2 cups broccoli
  - Macros: 45g protein, 50g carbs, 12g fat

**User Taps "Chat About This Meal"**
```
POST /api/v1/chat/start-text-session?agent_type=diet
    ↓
DietPlannerAgent loads:
    - User's meal plan
    - Dietary restrictions
    - Calorie target
    ↓
TextAgent ready in LiveKit room
```

**Chat Conversation:**
```
User: "Can I swap the sweet potato for rice?"
AI: [Checks meal plan, calculates macros]
"Absolutely! Use 1 cup of white rice (cooked) to match the carbs. 
Your macros will be nearly identical."

User: "What if I don't have broccoli?"
AI: "Any green veggie works - asparagus, green beans, or spinach. 
Same quantity. Want me to update your meal plan?"

User: "Yes please"
    ↓
Agent calls @llm_function update_meal(meal_id=..., substitution=...)
    ↓
MealPlan table updated in PostgreSQL
    ↓
AI: "Done! Updated for tonight and future meals. Enjoy dinner! 😊"
```

---

### **Day 2, 6:30 AM - Morning Routine**

**Push Notification:**
```
"Good morning! Time for your protein shake 🥤"
```

**User Asks General Question:**
```
User opens app: "Should I take creatine before or after workout?"
    ↓
POST /api/v1/chat/query
{
  "query": "Should I take creatine before or after workout?",
  "agent_type": null  // Auto-route
}
    ↓
AgentOrchestrator._classify_query() uses Claude Haiku:
    ↓
Determines: agent_type = "supplement"
    ↓
Routes to SupplementGuideAgent
    ↓
Agent response: "Timing doesn't matter much for creatine - it's 
about daily consistency. I recommend taking 5g after your workout 
with your post-workout meal for better absorption. Based on your 
profile, you're taking creatine monohydrate, which is perfect."
```

---

### **Day 5: Adaptation Kicks In**

**User Has Missed 2 Workouts**

**2:00 AM - Daily Recalculation (Celery Beat):**
```python
@celery_app.task
async def recalculate_plans():
    # Runs daily at 2 AM
    ↓
Finds users with recent missed sessions
    ↓
User missed Mon & Wed workouts
    ↓
AdaptivePlanningEngine analyzes:
    - Missed 2/3 planned workouts this week
    - Energy level = "low" (from recent logs)
    - Sleep quality = "poor" (from tracking)
    ↓
Decision: Reduce workout frequency from 5x/week to 3x/week
    ↓
WorkoutSchedule updated in PostgreSQL
    ↓
Notification queued: "I noticed you're busy this week. I've adjusted 
your plan to 3 full-body workouts. Quality over quantity! 💪"
```

**User Opens App:**
- Sees updated schedule
- New plan emphasizes compound movements
- Shorter, more intense sessions

---

### **Day 10: Progress Check-In**

**User Asks:**
```
"How am I doing?"
    ↓
Routes to TrackerAgent
    ↓
Agent queries PostgreSQL:
    - WorkoutLog: 6 workouts completed
    - MealPlan adherence: 80%
    - Weight trend: -2 lbs
    - Strength gains: +10 lbs on squat
    ↓
Response: "You're doing great! 6 workouts in 10 days, solid 
adherence. You've lost 2 pounds and added 10 pounds to your squat. 
That's exactly the progress we want - building strength while 
leaning out. Keep it up! 🔥"
```

---

### **Day 30: Voice Coaching Session**

**User Wants Motivation:**
```
User: "Start voice session - general chat"
    ↓
POST /api/v1/chat/start-voice-session?agent_type=general
    ↓
GeneralAssistantAgent with full context:
    - 30 days of workout history
    - Meal adherence patterns
    - Recent energy levels
    - Conversation history from Redis cache
    ↓
AI: "Hey! One month down - how are you feeling?"

User: "Honestly, a bit tired of chicken and rice"
AI: [Checks DietPlannerAgent history]
"I hear you! You've been super consistent with the same meals. 
Let's mix it up - how about trying salmon, ground turkey, or 
even a stir-fry? I can update your meal plan with 3 new dinner 
options. Want me to do that?"

User: "Yes please"
    ↓
Agent calls DietPlannerAgent.generate_meal_variations()
    ↓
New meals added to MealPlan table
    ↓
AI: "Done! Check your meal plan - you've got Thai Chicken Stir-Fry, 
Salmon with Asparagus, and Turkey Chili. All hit your macros. 
Variety keeps it sustainable! 🍽️"
```

---

### **Day 60: Plateau Management**

**Automatic Detection:**
```
Daily recalculation task notices:
    - Weight hasn't changed in 2 weeks
    - Workout weights plateaued
    - User still logging consistently
    ↓
AdaptivePlanningEngine triggers:
    - Increase workout volume (add 1 set per exercise)
    - Reduce calories by 200/day
    - Add 1 cardio session
    ↓
Notification: "I've noticed progress slowed down. I've made some 
adjustments to break through this plateau. Let's crush it! 💪"
```

---

## **Technical Flow Summary**

Every interaction follows this pattern:

1. **User Action** (tap, speak, text)
   ↓
2. **FastAPI Endpoint** receives request
   ↓
3. **LiveKit Room Created** (if voice/text session)
   ↓
4. **Agent Worker** picks up job from LiveKit
   ↓
5. **Agent loads context** from PostgreSQL/Redis
   ↓
6. **LLM processes** with specialized prompts + tools
   ↓
7. **Agent uses @llm_functions** to query/update database
   ↓
8. **Response generated** (text or voice)
   ↓
9. **Database updated** (logs, plans, progress)
   ↓
10. **Celery tasks** handle background work (notifications, recalculations)

---

## **Key User Benefits**

✅ **Natural Interaction**: Talk or type, AI understands context  
✅ **Real-time Coaching**: Voice guidance during workouts  
✅ **Automatic Adaptation**: Plans adjust to your reality  
✅ **Proactive Reminders**: Never miss a workout/meal  
✅ **Progress Tracking**: AI analyzes trends you might miss  
✅ **Continuous Improvement**: Gets smarter as it learns your patterns

The architecture creates a **truly personalized AI fitness coach** that feels like having a real trainer in your pocket 24/7.