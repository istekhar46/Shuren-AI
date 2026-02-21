# New Onboarding Flow - 4-Step Agent-Driven System

## Document Overview

This document defines the new 4-step onboarding flow for Shuren AI fitness application. This replaces the previous 9-step system with a streamlined, value-first approach where users see their complete workout and meal plans during onboarding.

**Last Updated:** February 20, 2026  
**Status:** Approved for Implementation  
**Replaces:** Previous 9-step onboarding system (no backward compatibility required)

---

## Core Philosophy

### Key Principles

1. **Immediate Value Delivery** - Users see their actual workout and meal plans during onboarding, not after
2. **Iterative Refinement** - Agents generate plans, users review and request changes, agents refine
3. **Tool-Based Persistence** - Agents use tool calls to save approved data to database
4. **Conversational Flow** - Natural chat interface with specialized agents
5. **Trust Building** - Users know exactly what they're committing to before completion

### Why This Change?

**Problems with 9-Step System:**
- Delayed gratification - users answer questions without seeing results
- Abstract data collection - gathering preferences without building plans
- Long perceived time - 9 steps feels overwhelming
- Trust gap - users don't know what they're getting until the end

**Benefits of 4-Step System:**
- 56% reduction in steps (9 → 4)
- Immediate value - users see plans in steps 2 and 3
- Higher engagement - concrete outputs keep users excited
- Better conversion - faster time to completion
- Clear expectations - users approve actual plans, not just preferences

---

## The 4-Step Flow

### Step 1: Fitness Assessment (Level + Goals)

**Agent:** Fitness Assessment Agent  
**Duration:** 3-5 minutes  
**Objective:** Understand who the user is and what they want to achieve

#### What Agent Collects:
- Fitness experience level (beginner / intermediate / advanced)
- Primary fitness goal (fat loss / muscle gain / general fitness)
- Optional secondary goal
- Years of training experience (if applicable)
- Current activity level

#### Conversation Flow:
```
Agent: "Hi! I'm here to help you build your personalized fitness plan. 
        Let's start with the basics - would you describe yourself as 
        a beginner, intermediate, or advanced in fitness?"

User: "I'm intermediate, been working out for about 2 years"

Agent: "Great! 2 years of consistent training puts you in a good position. 
        What's your primary fitness goal right now?"

User: "I want to lose fat but also build some muscle"

Agent: "Perfect - body recomposition. That's definitely achievable at your level.
        Would you say fat loss is the priority, or equal focus on both?"

User: "Fat loss is the main priority"

Agent: "Got it. I'll design your plan with fat loss as the primary goal 
        while preserving and building muscle. Ready to move on to your 
        workout plan?"
```

#### Data Saved (via tool call):
```json
{
  "fitness_level": "intermediate",
  "experience_years": 2,
  "primary_goal": "fat_loss",
  "secondary_goal": "muscle_gain",
  "goal_priority": "fat_loss_primary"
}
```

#### Tool Call:
```python
await agent.save_fitness_assessment(
    user_id=user_id,
    fitness_level="intermediate",
    experience_years=2,
    primary_goal="fat_loss",
    secondary_goal="muscle_gain"
)
```

---

### Step 2: Workout Planning (Constraints + Complete Plan)

**Agent:** Workout Planning Agent  
**Duration:** 8-12 minutes  
**Objective:** Generate and finalize a complete workout plan the user will follow

#### Phase 2A: Gather Constraints

**What Agent Collects:**
- Available equipment (gym / home / minimal)
- Specific equipment list (if home/minimal)
- Physical injuries or limitations
- Time availability (days per week, minutes per session)
- Workout location preference
- Any exercise dislikes or preferences

**Conversation Flow:**
```
Agent: "Now let's build your workout plan. First, where will you be training?"

User: "I have a gym membership"

Agent: "Perfect! Does your gym have all standard equipment - barbells, 
        dumbbells, machines, cables?"

User: "Yes, fully equipped"

Agent: "Great. Any injuries or physical limitations I should know about?"

User: "I have a minor shoulder issue, can't do overhead press with heavy weight"

Agent: "Noted - I'll avoid heavy overhead pressing and include shoulder-friendly 
        alternatives. How many days per week can you commit to training?"

User: "I can do 6 days"

Agent: "Excellent. And how much time per session?"

User: "About 60-75 minutes"

Agent: "Perfect. Let me design your workout plan..."
```

#### Phase 2B: Generate Workout Plan

**Agent generates a complete workout plan including:**
- Weekly split structure (e.g., 6-day push/pull/legs)
- Specific exercises for each day
- Sets, reps, and rest periods
- Progressive overload strategy
- Cardio/HIIT integration
- Rest days
- Duration (e.g., 24 weeks)

**Example Generated Plan:**
```
🏋️‍♂️ Your 6-Day Workout Plan (Fat Loss + Muscle Building)

General Principles:
✔️ Progressive overload - increase weight/reps weekly
✔️ HIIT cardio 3x/week for fat loss
✔️ Compound movements prioritized
✔️ Shoulder-friendly alternatives included

Weekly Split:

Day 1 – Chest + Triceps + Abs
• Warm-up: 5-7 min cardio
• Barbell Bench Press: 4×8-12
• Incline Dumbbell Press: 3×8-12
• Cable Chest Fly: 3×10-12
• Triceps Pushdowns: 3×10-12
• Overhead Triceps Extension (light): 3×12-15
• Abs Circuit: Planks + Leg Raises

Day 2 – Back + Biceps
• Pull-ups/Lat Pulldown: 4×8-12
• Bent-Over Barbell Rows: 3×8-10
• Seated Cable Rows: 3×10-12
• Face Pulls (shoulder health): 3×15
• Bicep Curls: 3×10-12
• Hammer Curls: 3×10-12

Day 3 – Legs + Lower Body
• Squats: 4×8-12
• Romanian Deadlifts: 3×8-10
• Leg Press: 3×10-12
• Lunges: 2×10 each leg
• Calf Raises: 3×15-20
• HIIT: 15 min (30s sprint / 90s walk)

Day 4 – Shoulders + Abs + Cardio
• Dumbbell Shoulder Press (moderate): 4×10-12
• Side Lateral Raises: 3×12-15
• Front Raises: 3×12-15
• Rear Delt Fly: 3×12-15
• Shrugs: 3×10-12
• Abs: Cable Woodchoppers + Crunches
• Steady Cardio: 20 min moderate

Day 5 – Full-Body Strength + HIIT
• Deadlifts: 3×5
• Bench Press: 3×8
• Barbell Rows: 3×8
• Kettlebell Swings: 3×15
• HIIT: 8 rounds (30s sprint / 90s walk)

Day 6 – Active Recovery
• Light jog or brisk walk: 30-40 min
• Stretching and mobility work
• Foam rolling

Day 7 – Complete Rest

Progressive Overload Strategy:
• Weeks 1-4: Learn form, moderate weight
• Weeks 5-12: Increase weight 2.5-5% when you hit top rep range
• Weeks 13-24: Continue progression, deload every 6 weeks
```

#### Phase 2C: User Review & Refinement

**Conversation Flow:**
```
Agent: "Here's your complete workout plan. It's designed for fat loss with 
        muscle building, 6 days per week, with shoulder-friendly exercises. 
        Take a look and let me know what you think!"

User: "This looks great! But I don't like lunges, can we swap that?"

Agent: "Absolutely! How about Bulgarian split squats or leg extensions instead?"

User: "Leg extensions work better for me"

Agent: "Perfect, I've updated Day 3 to include leg extensions instead of lunges.
        Anything else you'd like to adjust?"

User: "No, this looks perfect!"

Agent: "Excellent! I'm saving your workout plan now. You'll be able to see 
        it in your dashboard and I'll guide you through each workout."
```

#### Data Saved (via tool call):
```json
{
  "equipment": ["gym_full"],
  "injuries": ["shoulder_minor"],
  "limitations": ["no_heavy_overhead_press"],
  "days_per_week": 6,
  "minutes_per_session": 70,
  "workout_plan": {
    "plan_name": "6-Day Fat Loss + Muscle Building",
    "duration_weeks": 24,
    "split_type": "push_pull_legs_modified",
    "days": [
      {
        "day_number": 1,
        "name": "Chest + Triceps + Abs",
        "exercises": [
          {
            "name": "Barbell Bench Press",
            "sets": 4,
            "reps": "8-12",
            "rest_seconds": 90,
            "notes": "Progressive overload"
          }
          // ... more exercises
        ]
      }
      // ... more days
    ]
  }
}
```

#### Tool Calls:
```python
# Save constraints
await agent.save_workout_constraints(
    user_id=user_id,
    equipment=["gym_full"],
    injuries=["shoulder_minor"],
    limitations=["no_heavy_overhead_press"],
    days_per_week=6,
    minutes_per_session=70
)

# Save complete workout plan
await agent.save_workout_plan(
    user_id=user_id,
    plan_data={...}  # Full plan structure
)
```

---

### Step 3: Meal Planning (Preferences + Complete Plan with Timing)

**Agent:** Diet Planning Agent  
**Duration:** 10-15 minutes  
**Objective:** Generate and finalize a complete meal plan with timing

#### Phase 3A: Gather Diet Preferences

**What Agent Collects:**
- Diet type (omnivore / vegetarian / vegan / pescatarian / keto / paleo)
- Food allergies
- Food intolerances
- Foods they dislike
- Cuisine preferences
- Cooking skill level
- Meal frequency preference

**Conversation Flow:**
```
Agent: "Now let's create your meal plan. First, do you follow any specific 
        diet - vegetarian, vegan, keto, or are you an omnivore?"

User: "I'm an omnivore, I eat everything"

Agent: "Great! Any food allergies I should know about?"

User: "No allergies"

Agent: "How about intolerances or foods you strongly dislike?"

User: "I don't like fish much, and dairy sometimes bothers me"

Agent: "Noted - I'll minimize fish and dairy. How many meals per day 
        do you prefer?"

User: "I like eating 5-6 times a day, keeps me from getting too hungry"

Agent: "Perfect for your fat loss goal - frequent meals help manage hunger.
        What time do you usually wake up?"

User: "Around 5:30 AM, I work out at 6:30"

Agent: "Got it. And when do you typically go to bed?"

User: "Around 10 PM"

Agent: "Perfect. Let me create your meal plan with timing..."
```

#### Phase 3B: Generate Meal Plan

**Agent generates:**
- Daily calorie target (based on goal from Step 1)
- Macro split (protein/carbs/fats)
- Complete weekly meal template
- Meal timing aligned with workout schedule
- Specific meal suggestions
- Pre/post-workout nutrition
- Substitution options

**Example Generated Plan:**
```
🍽️ Your Personalized Meal Plan (Fat Loss - High Protein)

Daily Targets:
• Calories: 2,200 kcal (slight deficit for fat loss)
• Protein: 165g (30%)
• Carbs: 220g (40%)
• Fats: 73g (30%)

Daily Schedule:

5:30 AM - Wake Up
6:00 AM - Pre-Workout Snack
  • 1 banana + 5 soaked almonds + black coffee
  • OR 1 small apple + 2 dates + green tea
  • OR ½ cup watermelon + 5 walnuts

7:30 AM - Post-Workout Shake
  • Whey protein shake (1 scoop) + water
  • OR 250ml almond milk + 2 boiled eggs
  • OR 200g Greek yogurt + berries

8:00 AM - Breakfast
  Week 1 & 3:
    • 3 eggs (2 whole + 1 white) omelette with vegetables
    • 2 multigrain toasts
    • Optional: 1 glass almond milk
  
  Week 2 & 4:
    • ¾ cup oats cooked in almond milk
    • 1 tbsp peanut butter
    • Mixed berries
  
  Protein: ~30g | Calories: ~450

11:00 AM - Mid-Morning Snack
  • Sprout salad (1 bowl) with cucumber, onion, lemon
  • OR Mixed fruit + handful almonds
  • OR Hummus with veggie sticks
  
  Protein: ~10g | Calories: ~200

1:30 PM - Lunch
  Option 1: Grilled chicken (150g) + brown rice (¾ cup) + mixed veg + salad
  Option 2: Paneer (150g) + 2 rotis + dal + veg sabzi + salad
  Option 3: Soy chunks (50g) + quinoa + roasted vegetables
  
  Protein: ~40g | Calories: ~600

4:00 PM - Evening Snack
  • Boiled chana (chickpeas) + black tea
  • OR Protein smoothie (almond milk + banana + protein powder)
  • OR Roasted peanuts + fruit
  
  Protein: ~15g | Calories: ~250

7:30 PM - Dinner
  Option 1: Grilled chicken (150g) + vegetables + 1 roti
  Option 2: Egg curry (2 eggs) + brown rice + salad
  Option 3: Paneer tikka + dal + vegetables + 1 roti
  
  Protein: ~35g | Calories: ~550

9:30 PM - Before Bed (Optional)
  • Warm almond milk (200ml) + turmeric
  • OR Casein protein shake
  • OR Small bowl of curd
  
  Protein: ~10g | Calories: ~150

Weekly Rotation:
• Monday: Chicken-based meals
• Tuesday: Egg-based meals
• Wednesday: Paneer/vegetarian
• Thursday: Chicken-based meals
• Friday: Egg-based meals
• Saturday: Soy/vegetarian
• Sunday: Flexible (cheat-smart day)

Substitution Guide:
• Don't like chicken? → Use turkey, lean beef, or extra paneer
• Don't like eggs? → Use tofu scramble or extra protein shake
• Don't like brown rice? → Use quinoa, sweet potato, or extra rotis
• Dairy issues? → Use almond/soy milk, dairy-free yogurt

Meal Prep Tips:
• Prep proteins on Sunday (grill chicken, boil eggs)
• Pre-cut vegetables for the week
• Cook grains in batches
• Keep healthy snacks ready
```

#### Phase 3C: User Review & Refinement

**Conversation Flow:**
```
Agent: "Here's your complete meal plan with timing! It's designed for fat loss
        with high protein, minimal fish and dairy as you requested. 
        What do you think?"

User: "This is really detailed! But I see chicken a lot - can we add 
       more variety?"

Agent: "Absolutely! How about I add turkey, lean beef, and more vegetarian 
        options? Would you like me to include more soy-based meals?"

User: "Yes, more variety would be great. And can we move dinner to 8 PM? 
       I usually eat a bit later"

Agent: "Done! I've updated dinner to 8:00 PM and added more protein variety.
        Your evening snack is now at 4:30 PM to maintain good spacing.
        How does that look?"

User: "Perfect! This is exactly what I need"

Agent: "Excellent! I'm saving your meal plan now. You'll get notifications
        for each meal, and you can swap meals anytime through the app."
```

#### Data Saved (via tool call):
```json
{
  "diet_type": "omnivore",
  "allergies": [],
  "intolerances": ["dairy_mild"],
  "dislikes": ["fish"],
  "meal_frequency": 6,
  "daily_calorie_target": 2200,
  "protein_percentage": 30,
  "carbs_percentage": 40,
  "fats_percentage": 30,
  "meal_plan": {
    "plan_name": "High Protein Fat Loss",
    "daily_schedule": [
      {
        "meal_name": "Pre-Workout Snack",
        "scheduled_time": "06:00",
        "options": [
          {
            "description": "1 banana + 5 almonds + black coffee",
            "calories": 150,
            "protein": 3
          }
          // ... more options
        ]
      }
      // ... more meals
    ],
    "weekly_template": {
      // Full weekly rotation
    }
  }
}
```

#### Tool Calls:
```python
# Save diet preferences
await agent.save_diet_preferences(
    user_id=user_id,
    diet_type="omnivore",
    allergies=[],
    intolerances=["dairy_mild"],
    dislikes=["fish"]
)

# Save meal plan with timing
await agent.save_meal_plan(
    user_id=user_id,
    plan_data={...}  # Full meal plan structure
)

# Save meal schedules
await agent.save_meal_schedules(
    user_id=user_id,
    schedules=[
        {"meal_name": "Pre-Workout", "time": "06:00"},
        {"meal_name": "Post-Workout", "time": "07:30"},
        # ... more schedules
    ]
)
```

---

### Step 4: Lifestyle Setup (Hydration + Supplements)

**Agent:** Scheduling Agent  
**Duration:** 3-5 minutes  
**Objective:** Set up hydration reminders and supplement preferences

#### What Agent Collects:
- Daily water intake goal (ml)
- Hydration reminder frequency
- Interest in supplement guidance
- Current supplements (if any)
- Reminder preferences

**Conversation Flow:**
```
Agent: "Almost done! Let's set up your hydration and supplement reminders.
        How much water do you typically drink per day?"

User: "Probably around 2 liters, but I forget sometimes"

Agent: "That's a good baseline. For your activity level and fat loss goal,
        I'd recommend 3 liters per day. Would you like reminders?"

User: "Yes, that would help"

Agent: "Great! How often should I remind you? Every hour, every 2 hours?"

User: "Every 2 hours works"

Agent: "Perfect. Now, are you interested in supplement guidance? I can provide
        science-based recommendations for your goals."

User: "Yes, I'm interested. I currently take whey protein and a multivitamin"

Agent: "Excellent! Those are great basics. I'll provide personalized supplement
        recommendations in your dashboard. You can always ask me about specific
        supplements anytime."

User: "Sounds good!"

Agent: "Perfect! Your onboarding is complete. Let me save everything..."
```

#### Data Saved (via tool call):
```json
{
  "daily_water_target_ml": 3000,
  "reminder_frequency_minutes": 120,
  "enable_hydration_reminders": true,
  "interested_in_supplements": true,
  "current_supplements": ["whey_protein", "multivitamin"]
}
```

#### Tool Calls:
```python
# Save hydration preferences
await agent.save_hydration_preferences(
    user_id=user_id,
    daily_water_target_ml=3000,
    reminder_frequency_minutes=120,
    enable_reminders=true
)

# Save supplement preferences
await agent.save_supplement_preferences(
    user_id=user_id,
    interested=true,
    current_supplements=["whey_protein", "multivitamin"]
)

# Mark onboarding complete
await agent.complete_onboarding(user_id=user_id)
```

---

## Onboarding Completion

### What Happens After Step 4:

1. **Profile Creation**
   - All collected data is consolidated
   - `UserProfile` entity created with `is_locked=True`
   - All related entities created (goals, constraints, meal plans, schedules)
   - Initial `UserProfileVersion` snapshot created

2. **User Dashboard Unlocked**
   - User gains access to general chat interface
   - Can see their complete workout plan
   - Can see their complete meal plan
   - Can view schedules and reminders

3. **First Day Guidance**
   - System shows today's workout (if workout day)
   - Shows next meal and timing
   - Provides welcome message with next steps

4. **Agent Handoff**
   - User is now routed to General Assistant agent
   - All onboarding agents' context is available
   - User can ask questions, request modifications, track progress

---

## Technical Architecture

### Agent Tool Calls

Each agent has access to specialized tools for saving data:

**Fitness Assessment Agent Tools:**
- `save_fitness_assessment(user_id, fitness_level, goals, ...)`

**Workout Planning Agent Tools:**
- `save_workout_constraints(user_id, equipment, injuries, ...)`
- `save_workout_plan(user_id, plan_data)`
- `generate_workout_plan(constraints, goals)` - LLM-powered generation

**Diet Planning Agent Tools:**
- `save_diet_preferences(user_id, diet_type, allergies, ...)`
- `save_meal_plan(user_id, plan_data)`
- `save_meal_schedules(user_id, schedules)`
- `generate_meal_plan(preferences, goals, timing)` - LLM-powered generation

**Scheduling Agent Tools:**
- `save_hydration_preferences(user_id, water_target, ...)`
- `save_supplement_preferences(user_id, interested, current)`
- `complete_onboarding(user_id)`

### Database Schema Changes

**New Tables:**

```sql
-- Stores complete workout plans
CREATE TABLE workout_plans (
    id UUID PRIMARY KEY,
    profile_id UUID REFERENCES user_profiles(id),
    plan_name VARCHAR(255),
    plan_description TEXT,
    duration_weeks INTEGER,
    days_per_week INTEGER,
    plan_data JSONB,  -- Full workout structure
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Stores complete meal plan templates
CREATE TABLE meal_plan_templates (
    id UUID PRIMARY KEY,
    profile_id UUID REFERENCES user_profiles(id),
    plan_name VARCHAR(255),
    daily_calorie_target INTEGER,
    protein_percentage DECIMAL,
    carbs_percentage DECIMAL,
    fats_percentage DECIMAL,
    weekly_template JSONB,  -- Full meal structure
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Modified Tables:**

```sql
-- OnboardingState simplified
ALTER TABLE onboarding_states
    DROP COLUMN step_data,  -- No longer needed
    ADD COLUMN current_step INTEGER DEFAULT 1,  -- Now 1-4 instead of 0-9
    ADD COLUMN step_1_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_2_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_3_complete BOOLEAN DEFAULT FALSE,
    ADD COLUMN step_4_complete BOOLEAN DEFAULT FALSE;
```

### API Endpoints

**New Endpoints:**

```
POST /api/v1/onboarding/chat
  - Send message to current onboarding agent
  - Returns agent response

GET /api/v1/onboarding/current-step
  - Returns current step number and agent type

POST /api/v1/onboarding/generate-workout-plan
  - Triggers workout plan generation
  - Returns generated plan for review

POST /api/v1/onboarding/save-workout-plan
  - Saves approved workout plan
  - Advances to step 3

POST /api/v1/onboarding/generate-meal-plan
  - Triggers meal plan generation
  - Returns generated plan for review

POST /api/v1/onboarding/save-meal-plan
  - Saves approved meal plan
  - Advances to step 4

POST /api/v1/onboarding/complete
  - Completes onboarding
  - Creates profile and unlocks dashboard
```

---

## Migration Strategy

### No Backward Compatibility Required

Since backward compatibility is not needed:

1. **Database Migration**
   - Drop old onboarding_states data
   - Create new tables (workout_plans, meal_plan_templates)
   - Modify onboarding_states schema
   - All existing users will need to re-onboard

2. **Code Cleanup**
   - Remove old 9-step validation logic
   - Remove old OnboardingService methods
   - Remove old STATE_METADATA
   - Clean up unused endpoints

3. **Agent Implementation**
   - Implement new agent tool functions
   - Add LLM-powered plan generation
   - Add plan refinement logic
   - Test agent conversations

4. **Frontend Updates**
   - Update onboarding UI to 4-step flow
   - Add plan preview/review components
   - Add plan refinement interface
   - Update progress indicators

---

## Success Metrics

### Key Performance Indicators:

1. **Completion Rate**
   - Target: >85% (vs ~60% with 9-step)
   - Measure: Users who complete all 4 steps

2. **Time to Complete**
   - Target: <25 minutes average
   - Measure: Time from start to completion

3. **User Satisfaction**
   - Target: >4.5/5 rating
   - Measure: Post-onboarding survey

4. **Plan Approval Rate**
   - Target: >90% approve on first or second iteration
   - Measure: Number of refinement requests per plan

5. **Engagement After Onboarding**
   - Target: >70% active in first week
   - Measure: Users who log workouts or meals

---

## Appendix

### Example Complete Workout Plan JSON

```json
{
  "plan_name": "6-Day Fat Loss + Muscle Building",
  "duration_weeks": 24,
  "days_per_week": 6,
  "split_type": "push_pull_legs_modified",
  "progressive_overload_strategy": "Increase weight 2.5-5% when hitting top rep range",
  "days": [
    {
      "day_number": 1,
      "name": "Chest + Triceps + Abs",
      "focus": "Upper body push",
      "estimated_duration_minutes": 70,
      "exercises": [
        {
          "order": 1,
          "name": "Warm-up Cardio",
          "type": "cardio",
          "duration_minutes": 7,
          "intensity": "light"
        },
        {
          "order": 2,
          "name": "Barbell Bench Press",
          "type": "compound",
          "muscle_groups": ["chest", "triceps", "shoulders"],
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "tempo": "2-0-2-0",
          "notes": "Progressive overload - increase weight when you hit 12 reps",
          "video_url": "https://example.com/bench-press.gif"
        },
        {
          "order": 3,
          "name": "Incline Dumbbell Press",
          "type": "compound",
          "muscle_groups": ["upper_chest", "shoulders"],
          "sets": 3,
          "reps": "8-12",
          "rest_seconds": 90,
          "tempo": "2-0-2-0",
          "notes": "Focus on upper chest development"
        }
        // ... more exercises
      ]
    }
    // ... more days
  ]
}
```

### Example Complete Meal Plan JSON

```json
{
  "plan_name": "High Protein Fat Loss",
  "daily_calorie_target": 2200,
  "protein_grams": 165,
  "carbs_grams": 220,
  "fats_grams": 73,
  "meal_frequency": 6,
  "daily_schedule": [
    {
      "meal_name": "Pre-Workout Snack",
      "scheduled_time": "06:00",
      "meal_type": "snack",
      "target_calories": 150,
      "target_protein": 3,
      "options": [
        {
          "option_number": 1,
          "description": "1 banana + 5 soaked almonds + black coffee",
          "ingredients": [
            {"name": "Banana", "quantity": 1, "unit": "medium"},
            {"name": "Almonds", "quantity": 5, "unit": "pieces"},
            {"name": "Black Coffee", "quantity": 1, "unit": "cup"}
          ],
          "calories": 150,
          "protein": 3,
          "carbs": 30,
          "fats": 3,
          "prep_time_minutes": 2
        },
        {
          "option_number": 2,
          "description": "1 small apple + 2 dates + green tea",
          "ingredients": [
            {"name": "Apple", "quantity": 1, "unit": "small"},
            {"name": "Dates", "quantity": 2, "unit": "pieces"},
            {"name": "Green Tea", "quantity": 1, "unit": "cup"}
          ],
          "calories": 140,
          "protein": 2,
          "carbs": 35,
          "fats": 1,
          "prep_time_minutes": 2
        }
      ]
    }
    // ... more meals
  ],
  "weekly_rotation": {
    "monday": {
      "breakfast": "option_1",
      "lunch": "option_1",
      "dinner": "option_1"
    }
    // ... more days
  },
  "substitution_rules": [
    {
      "original": "chicken",
      "alternatives": ["turkey", "lean_beef", "paneer"],
      "reason": "Protein variety"
    }
    // ... more substitutions
  ]
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-20 | System | Initial document creation |

