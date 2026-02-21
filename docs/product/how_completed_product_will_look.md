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

**3. Specialized Agent Onboarding (Voice or Text)**
- User chooses: "Talk to AI Coach" or "Chat with AI Coach"

**Onboarding Flow with Specialized Agents:**

```
=== STEP 1-2: FITNESS ASSESSMENT AGENT ===

User taps "Start Onboarding"
    ↓
App calls: POST /api/v1/onboarding/chat
    ↓
FastAPI routes to Fitness Assessment Agent
    ↓
Agent loads: empty context (first agent)
    ↓
AI: "Hi! I'm your Fitness Assessment Agent. I'll help understand your 
current fitness level. How would you describe your exercise experience - 
are you a beginner, intermediate, or advanced?"
    ↓
User: "I've been working out for about 2 years, so intermediate"
    ↓
Agent: "Great! 2 years of experience. Do you currently have access to 
a gym, or do you prefer working out at home?"
    ↓
User: "I have a gym membership"
    ↓
Agent: "Perfect! Any physical limitations or injuries I should know about?"
    ↓
User: "No, I'm good"
    ↓
Agent calls: save_fitness_assessment(
    fitness_level="intermediate",
    experience_years=2,
    location="gym",
    limitations=[]
)
    ↓
PostgreSQL: Updates OnboardingState.agent_context
    ↓
Agent: "Excellent! I've saved your fitness assessment. Let's move on 
to defining your goals."

=== STEP 3: GOAL SETTING AGENT ===

System advances to Goal Setting Agent
    ↓
Agent loads context: {
    "fitness_assessment": {
        "fitness_level": "intermediate",
        "location": "gym"
    }
}
    ↓
AI: "Hi! I'm your Goal Setting Agent. Based on your intermediate fitness 
level, what's your primary goal - building muscle, losing fat, or general fitness?"
    ↓
User: "I want to build muscle"
    ↓
Agent: "Awesome! Building muscle is a great goal. Do you have any 
secondary goals, like improving strength or endurance?"
    ↓
User: "Maybe lose a bit of belly fat too"
    ↓
Agent: "Perfect combination! Muscle gain with some fat loss. Do you 
have a target weight in mind?"
    ↓
User: "I'm 70kg now, want to get to 75kg"
    ↓
Agent calls: save_fitness_goals(
    primary_goal="muscle_gain",
    secondary_goal="fat_loss",
    target_weight_kg=75
)
    ↓
PostgreSQL: Updates OnboardingState.agent_context
    ↓
Agent: "Got it! Primary goal: muscle gain, target weight: 75kg. 
Now let's create your workout plan."

=== STEP 4-5: WORKOUT PLANNING AGENT ===

System advances to Workout Planning Agent
    ↓
Agent loads context: {
    "fitness_assessment": {...},
    "goal_setting": {
        "primary_goal": "muscle_gain",
        "target_weight_kg": 75
    }
}
    ↓
AI: "Hi! I'm your Workout Planning Agent. I'll create a personalized 
workout plan for you. How many days per week can you commit to training?"
    ↓
User: "4 days a week"
    ↓
Agent: "Perfect! 4 days is ideal for muscle gain. How much time do 
you have per session?"
    ↓
User: "About an hour"
    ↓
Agent: "Great! Let me create a plan for you..."
    ↓
Agent calls: generate_workout_plan(
    frequency=4,
    location="gym",
    duration_minutes=60,
    goal="muscle_gain",
    fitness_level="intermediate"
)
    ↓
WorkoutService generates plan
    ↓
Agent: "Here's your personalized 4-day workout plan:

📅 **Upper/Lower Split**
- **Day 1: Upper Body Push** (Chest, Shoulders, Triceps)
  - Bench Press: 4 sets x 8-10 reps
  - Overhead Press: 3 sets x 8-10 reps
  - Incline Dumbbell Press: 3 sets x 10-12 reps
  - Lateral Raises: 3 sets x 12-15 reps
  - Tricep Dips: 3 sets x 10-12 reps

- **Day 2: Lower Body** (Quads, Hamstrings, Glutes)
  - Squats: 4 sets x 8-10 reps
  - Romanian Deadlifts: 3 sets x 10-12 reps
  - Leg Press: 3 sets x 12-15 reps
  - Leg Curls: 3 sets x 12-15 reps
  - Calf Raises: 4 sets x 15-20 reps

- **Day 3: Rest**

- **Day 4: Upper Body Pull** (Back, Biceps)
  - Deadlifts: 4 sets x 6-8 reps
  - Pull-ups: 3 sets x 8-10 reps
  - Barbell Rows: 3 sets x 8-10 reps
  - Face Pulls: 3 sets x 15-20 reps
  - Bicep Curls: 3 sets x 10-12 reps

- **Day 5: Lower Body & Core**
  - Front Squats: 3 sets x 10-12 reps
  - Bulgarian Split Squats: 3 sets x 10-12 reps each
  - Leg Extensions: 3 sets x 12-15 reps
  - Planks: 3 sets x 60 seconds
  - Hanging Leg Raises: 3 sets x 12-15 reps

- **Days 6-7: Rest**

This plan hits each muscle group twice per week with optimal volume 
for muscle growth. Each session is 60-75 minutes. 

**Does this plan work for you?** You can approve it or request modifications."
    ↓
User: "Looks perfect!"
    ↓
Agent calls: save_workout_plan(
    plan_data={...},
    user_approved=True
)
    ↓
PostgreSQL: Saves workout plan to user profile
    ↓
Agent: "Excellent! Your workout plan is saved. Now let's talk about 
your nutrition to support muscle growth."

=== STEP 6-7: DIET PLANNING AGENT ===

System advances to Diet Planning Agent
    ↓
Agent loads context: {
    "fitness_assessment": {...},
    "goal_setting": {...},
    "workout_planning": {
        "frequency": 4,
        "plan_saved": true
    }
}
    ↓
AI: "Hi! I'm your Diet Planning Agent. To support your muscle gain 
goal with 4 workouts per week, we need proper nutrition. First, do 
you have any dietary restrictions - vegetarian, vegan, or any allergies?"
    ↓
User: "I'm non-veg, no allergies"
    ↓
Agent: "Perfect! That gives us lots of options. How many meals per 
day do you prefer?"
    ↓
User: "4 meals"
    ↓
Agent: "Great! 4 meals works well for muscle gain. Let me create 
your meal plan..."
    ↓
Agent calls: generate_meal_plan(
    goal="muscle_gain",
    diet_type="non_veg",
    meal_frequency=4,
    workout_frequency=4,
    current_weight_kg=70,
    target_weight_kg=75
)
    ↓
MealService generates plan
    ↓
Agent: "Here's your personalized meal plan:

🍽️ **Daily Nutrition Targets**
- Calories: 2,800 kcal
- Protein: 175g (25%)
- Carbs: 350g (50%)
- Fats: 78g (25%)

**Sample Day:**

**Meal 1 - Breakfast (7:00 AM)**
- 4 whole eggs scrambled
- 2 slices whole wheat toast
- 1 banana
- Macros: 600 kcal | 35g protein | 60g carbs | 22g fat

**Meal 2 - Lunch (12:00 PM)**
- 200g grilled chicken breast
- 1 cup brown rice
- Mixed vegetables
- Macros: 700 kcal | 55g protein | 80g carbs | 12g fat

**Meal 3 - Pre-Workout Snack (4:00 PM)**
- Protein shake with banana
- Handful of almonds
- Macros: 400 kcal | 30g protein | 45g carbs | 12g fat

**Meal 4 - Dinner (8:00 PM)**
- 200g salmon
- Sweet potato
- Broccoli
- Macros: 650 kcal | 50g protein | 70g carbs | 18g fat

**Meal 5 - Before Bed (Optional)**
- Greek yogurt with berries
- Macros: 250 kcal | 20g protein | 30g carbs | 8g fat

This plan provides enough protein for muscle growth and carbs for 
energy during workouts. 

**Does this meal plan work for you?** You can approve it or request modifications."
    ↓
User: "Yes, this looks good!"
    ↓
Agent calls: save_meal_plan(
    plan_data={...},
    user_approved=True
)
    ↓
PostgreSQL: Saves meal plan to user profile
    ↓
Agent: "Perfect! Your meal plan is saved. Now let's set up your 
daily schedule."

=== STEP 8-9: SCHEDULING AGENT ===

System advances to Scheduling Agent
    ↓
Agent loads context: {
    "fitness_assessment": {...},
    "goal_setting": {...},
    "workout_planning": {...},
    "diet_planning": {
        "meal_frequency": 4,
        "plan_saved": true
    }
}
    ↓
AI: "Hi! I'm your Scheduling Agent. Let's set up when you'll workout 
and eat. Which days work best for your 4 workouts?"
    ↓
User: "Monday, Tuesday, Thursday, Friday"
    ↓
Agent: "Great split! What time do you prefer to workout?"
    ↓
User: "Around 5:30 PM"
    ↓
Agent: "Perfect! Now for your meals - what time do you usually have breakfast?"
    ↓
User: "7 AM"
    ↓
Agent: "And lunch?"
    ↓
User: "12 PM"
    ↓
Agent: "Dinner?"
    ↓
User: "8 PM"
    ↓
Agent: "Great! I'll set up reminders for your workouts and meals. 
Do you want hydration reminders too?"
    ↓
User: "Yes, every 2 hours"
    ↓
Agent calls: save_schedules(
    workout_days=["monday", "tuesday", "thursday", "friday"],
    workout_time="17:30",
    meal_times=["07:00", "12:00", "16:00", "20:00"],
    hydration_frequency_minutes=120
)
    ↓
PostgreSQL: Saves all schedules to user profile
    ↓
Agent: "Perfect! All your schedules are set. You're all done with onboarding!"

=== ONBOARDING COMPLETE ===

System calls: complete_onboarding(user_id)
    ↓
Creates locked UserProfile with all data
    ↓
Marks onboarding_completed = True
    ↓
User sees: "🎉 Your personalized fitness plan is ready!"
    ↓
App navigates to main dashboard
```

**Behind the scenes:**
- Each agent saves data incrementally to user profile
- Context is passed between agents via `OnboardingState.agent_context`
- Conversation history stored per agent
- PostgreSQL updates in real-time
- Redis caches progress

**Post-Onboarding:**
- Only General Assistant Agent is available
- General Assistant has full access to user profile
- Can answer: "What's my workout today?", "What are my meals?", etc.

---

### **Day 1 Evening: First Workout**

**5:30 PM - Scheduled Workout Time**

**Push Notification:**
```
Celery Beat runs send_workout_reminders every 15 minutes
    ↓
Finds user has workout scheduled at 5:30 PM
    ↓
Sends FCM push: "Upper Body Push Day! Ready to crush it? 💪"
```

**User Opens App:**
- Sees today's workout: Upper Body Push
  - Bench Press: 4 sets x 8-10 reps
  - Overhead Press: 3 sets x 8-10 reps
  - Incline Dumbbell Press: 3 sets x 10-12 reps
  - Lateral Raises: 3 sets x 12-15 reps
  - Tricep Dips: 3 sets x 10-12 reps

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
AI Coach: "Alright! Let's crush this upper body push day. We're starting 
with bench press - 4 sets of 8-10 reps. Got your weight loaded?"
```

**During Workout:**
```
User: "Starting first set"
AI: "Perfect form! Remember - chest up, controlled descent. 
Let me know when you finish."

[30 seconds later]
User: "Done, 8 reps with 185 pounds"
    ↓
Agent calls @llm_function log_set_completion(exercise="Bench Press", reps=8, weight=185)
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
User: "Just finished tricep dips!"
AI: "That's it! Upper body push complete - crushed it! 🔥 
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
User has dinner scheduled 8:00 PM
    ↓
FCM push: "Dinner time! Check your meal plan 🍽️"
```

**User Opens Meal Plan:**
- Sees: 200g Salmon with Sweet Potato & Broccoli
  - 200g salmon
  - 1 medium sweet potato
  - 2 cups broccoli
  - Macros: 650 kcal | 50g protein | 70g carbs | 18g fat

**User Taps "Chat About This Meal"**
```
POST /api/v1/chat/query
{
  "query": "Can I swap the salmon for chicken?",
  "agent_type": "diet"
}
    ↓
Routes to DietPlannerAgent (General Assistant post-onboarding)
    ↓
Agent loads user's meal plan and preferences
```

**Chat Conversation:**
```
User: "Can I swap the salmon for chicken?"
AI: [Checks meal plan, calculates macros]
"Absolutely! Use 250g chicken breast to match the protein. 
Your macros will be nearly identical - 640 kcal | 52g protein | 70g carbs | 15g fat."

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
"Good morning! Time for breakfast 🥤"
```

**User Asks General Question:**
```
User opens app: "What's my workout today?"
    ↓
POST /api/v1/chat/query
{
  "query": "What's my workout today?",
  "agent_type": null  // Auto-route to General Assistant
}
    ↓
General Assistant Agent loads full user profile
    ↓
Agent response: "Today is Tuesday - Lower Body day! You'll be doing:
- Squats: 4 sets x 8-10 reps
- Romanian Deadlifts: 3 sets x 10-12 reps
- Leg Press: 3 sets x 12-15 reps
- Leg Curls: 3 sets x 12-15 reps
- Calf Raises: 4 sets x 15-20 reps

Your workout is scheduled for 5:30 PM. Ready to crush leg day? 💪"
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
    - Missed 2/4 planned workouts this week
    - Energy level = "low" (from recent logs)
    - Sleep quality = "poor" (from tracking)
    ↓
Decision: Reduce workout frequency from 4x/week to 3x/week
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
Routes to General Assistant Agent
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
3. **Agent Orchestrator** determines appropriate agent
   ↓
4. **Specialized Agent** loads context from PostgreSQL
   ↓
5. **LLM processes** with agent-specific prompts + tools
   ↓
6. **Agent uses tools** to query/update database
   ↓
7. **Response generated** (text or voice)
   ↓
8. **Database updated** (logs, plans, progress)
   ↓
9. **Celery tasks** handle background work (notifications, recalculations)

---

## **Key User Benefits**

✅ **Personalized Onboarding**: Each step guided by specialized agent with domain expertise  
✅ **Plan Approval**: Users see and approve workout/meal plans before saving  
✅ **Progressive Context**: Each agent has full context from previous steps  
✅ **Natural Interaction**: Talk or type, AI understands context  
✅ **Real-time Coaching**: Voice guidance during workouts  
✅ **Automatic Adaptation**: Plans adjust to your reality  
✅ **Proactive Reminders**: Never miss a workout/meal  
✅ **Progress Tracking**: AI analyzes trends you might miss  
✅ **Continuous Improvement**: Gets smarter as it learns your patterns

The architecture creates a **truly personalized AI fitness coach** that feels like having a real trainer in your pocket 24/7.
