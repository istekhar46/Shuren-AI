# Backend Schema Design Document
## AI-Powered Personal Fitness Application - Onboarding System

**Document Version:** 1.0  
**Last Updated:** January 28, 2026  
**Author:** Engineering Team  
**Status:** Draft for Review

---

## Table of Contents
1. [Overview](#overview)
2. [Database Technology Stack](#database-technology-stack)
3. [Schema Design Principles](#schema-design-principles)
4. [Core Entities](#core-entities)
5. [Relationship Diagram](#relationship-diagram)
6. [Detailed Table Specifications](#detailed-table-specifications)
7. [Indexes and Performance](#indexes-and-performance)
8. [Data Validation Rules](#data-validation-rules)
9. [Migration Strategy](#migration-strategy)
10. [API Considerations](#api-considerations)
11. [Security & Privacy](#security-and-privacy)

---

## 1. Overview

This document defines the database schema for the onboarding module of the AI-powered fitness application. The schema is designed to support:

- One-time mandatory onboarding flow
- Immutable historical tracking of user preferences
- Flexible querying for AI agent context
- Audit trail for plan modifications
- GDPR-compliant data handling

**Key Requirements:**
- Support 1M+ users at scale
- Sub-100ms read latency for user profile queries
- Versioned configuration changes
- Multi-region replication support
- Point-in-time recovery capability

---

## 2. Database Technology Stack

### Recommended Primary Database
**PostgreSQL 15+**

**Rationale:**
- JSONB support for flexible preference storage
- Strong ACID compliance for onboarding state management
- Excellent performance with proper indexing
- Rich constraint validation support
- Mature replication and backup tooling

### Alternative Considerations
- **MySQL 8.0+**: If team has existing MySQL expertise
- **Aurora PostgreSQL**: For AWS-native deployments with read scaling needs

### Caching Layer
- **Redis 7.0+**: For session state and frequently accessed user profiles
- Cache invalidation on profile updates
- TTL: 24 hours for active user profiles

---

## 3. Schema Design Principles

### Normalization Strategy
- **Third Normal Form (3NF)** for core entities
- Denormalization permitted for read-heavy aggregates
- Reference data stored in lookup tables

### Design Decisions
1. **Separate onboarding state from operational data**: Allows clean onboarding completion detection
2. **Versioned preferences**: Track all changes with timestamps for audit and rollback
3. **Enum tables over string literals**: Type safety and consistency
4. **Soft deletes**: Maintain data lineage, GDPR right-to-erasure via anonymization
5. **UTC timestamps throughout**: Timezone conversions handled at application layer

### Naming Conventions
- Tables: `snake_case`, plural nouns (e.g., `users`, `meal_plans`)
- Columns: `snake_case`
- Primary keys: `id` (UUID or BIGSERIAL)
- Foreign keys: `{table_singular}_id` (e.g., `user_id`)
- Timestamps: `created_at`, `updated_at`, `deleted_at`
- Booleans: `is_*` or `has_*` prefix

---

## 4. Core Entities

The schema is organized around these core entities:

```
users                           # Core user identity
├── onboarding_states           # Onboarding flow progress
├── user_profiles               # Current active configuration
├── user_profile_versions       # Historical configuration changes
├── fitness_goals               # Goal definitions and relationships
├── physical_constraints        # Equipment, injuries, limitations
├── dietary_preferences         # Diet type, restrictions, allergies
├── meal_plans                  # Structured meal plan configuration
├── meal_schedules              # Timing for each meal
├── workout_schedules           # Workout days and timing
├── hydration_preferences       # Hydration reminder configuration
└── lifestyle_baselines         # Energy, stress, sleep data
```

---

## 5. Relationship Diagram

```
┌─────────────┐
│   users     │
└──────┬──────┘
       │
       ├─────────────────┬───────────────────┬──────────────────┬──────────────────┐
       │                 │                   │                  │                  │
       ▼                 ▼                   ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────┐    ┌──────────────┐  ┌─────────────┐  ┌─────────────┐
│ onboarding_  │  │user_profiles│    │fitness_goals │  │meal_plans   │  │workout_     │
│   states     │  │             │    │              │  │             │  │ schedules   │
└──────────────┘  └──────┬──────┘    └──────────────┘  └─────────────┘  └─────────────┘
                         │
                         ├────────────┬───────────────┬──────────────────┐
                         ▼            ▼               ▼                  ▼
                  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                  │ physical_   │ │ dietary_    │ │meal_        │ │hydration_   │
                  │ constraints │ │ preferences │ │schedules    │ │preferences  │
                  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 6. Detailed Table Specifications

### 6.1 users

**Purpose:** Core user identity and authentication reference

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- External identity (from Auth0, Cognito, etc.)
    external_auth_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Basic info
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Account status
    account_status VARCHAR(50) NOT NULL DEFAULT 'active',
        -- Values: 'active', 'suspended', 'deleted'
    
    -- Onboarding tracking
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_external_auth_id ON users(external_auth_id);
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_onboarding ON users(onboarding_completed, created_at);
```

**Indexes Rationale:**
- `external_auth_id`: Fast authentication lookups
- `email`: User search and duplicate detection
- `onboarding_completed`: Dashboard queries for incomplete onboardings

---

### 6.2 onboarding_states

**Purpose:** Track user progress through onboarding flow, enable resume capability

```sql
CREATE TABLE onboarding_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Progress tracking
    current_step INTEGER NOT NULL DEFAULT 0,
        -- Maps to step numbers 0-11 from specification
    completed_steps INTEGER[] DEFAULT ARRAY[]::INTEGER[],
    
    -- State data (stores intermediate inputs before confirmation)
    step_data JSONB DEFAULT '{}'::jsonb,
        -- Key format: "step_1", "step_2", etc.
        -- Allows recovery if user drops off mid-flow
    
    -- Flow metadata
    flow_version VARCHAR(10) NOT NULL DEFAULT '1.0',
        -- Tracks which onboarding spec version user experienced
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Session tracking
    session_id VARCHAR(255),
    device_type VARCHAR(50),
    user_agent TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_current_step CHECK (current_step >= 0 AND current_step <= 11),
    CONSTRAINT unique_user_onboarding UNIQUE(user_id)
);

CREATE INDEX idx_onboarding_user_id ON onboarding_states(user_id);
CREATE INDEX idx_onboarding_incomplete ON onboarding_states(user_id, completed_at) 
    WHERE completed_at IS NULL;
CREATE INDEX idx_onboarding_last_activity ON onboarding_states(last_activity_at) 
    WHERE completed_at IS NULL;
```

**Design Notes:**
- `step_data` JSONB allows flexible storage without schema changes
- `completed_steps` array enables non-linear navigation if needed in future
- `session_id` supports analytics for drop-off analysis
- `flow_version` critical for A/B testing and migration handling

---

### 6.3 user_profiles

**Purpose:** Current active user configuration (single source of truth for AI agents)

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Version control
    version INTEGER NOT NULL DEFAULT 1,
    previous_version_id UUID REFERENCES user_profile_versions(id),
    
    -- Step 1: Fitness Experience
    fitness_level VARCHAR(50) NOT NULL,
        -- Values: 'beginner', 'intermediate', 'advanced'
    
    -- Step 2: Primary Goals
    primary_goal VARCHAR(50) NOT NULL,
        -- Values: 'fat_loss', 'muscle_gain', 'general_fitness'
    secondary_goal VARCHAR(50),
    
    -- Step 9: Lifestyle Baseline
    energy_level VARCHAR(50) NOT NULL,
        -- Values: 'low', 'medium', 'high'
    stress_level VARCHAR(50) NOT NULL,
        -- Values: 'low', 'medium', 'high'
    sleep_quality VARCHAR(50) NOT NULL,
        -- Values: 'poor', 'fair', 'good', 'excellent'
    
    -- References to related entities
    -- (detailed preferences stored in normalized tables)
    
    -- Modification tracking
    last_modified_by VARCHAR(50) NOT NULL DEFAULT 'user',
        -- Values: 'user', 'admin', 'system'
    modification_reason TEXT,
    
    -- Lock status
    is_locked BOOLEAN DEFAULT TRUE,
        -- Prevents accidental modifications
    locked_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_fitness_level CHECK (
        fitness_level IN ('beginner', 'intermediate', 'advanced')
    ),
    CONSTRAINT valid_primary_goal CHECK (
        primary_goal IN ('fat_loss', 'muscle_gain', 'general_fitness')
    ),
    CONSTRAINT valid_energy_level CHECK (
        energy_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT valid_stress_level CHECK (
        stress_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT valid_sleep_quality CHECK (
        sleep_quality IN ('poor', 'fair', 'good', 'excellent')
    )
);

CREATE UNIQUE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_goals ON user_profiles(primary_goal, secondary_goal);
CREATE INDEX idx_user_profiles_updated ON user_profiles(updated_at DESC);
```

**Design Notes:**
- Enforces enum values at database level
- `is_locked` implements "no silent changes" principle
- `version` increments on each update
- Direct reference to previous version enables quick rollback

---

### 6.4 user_profile_versions

**Purpose:** Immutable audit log of all profile changes

```sql
CREATE TABLE user_profile_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    
    -- Snapshot of profile at this version
    profile_snapshot JSONB NOT NULL,
        -- Complete copy of user_profiles row at time of change
    
    -- Change metadata
    changed_fields TEXT[],
        -- List of fields modified in this version
    change_reason TEXT,
    changed_by VARCHAR(50) NOT NULL,
        -- 'user', 'admin', 'system'
    
    -- Timestamps
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE,
        -- NULL for current version
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_version UNIQUE(user_id, version)
);

CREATE INDEX idx_profile_versions_user_id ON user_profile_versions(user_id, version DESC);
CREATE INDEX idx_profile_versions_valid_from ON user_profile_versions(valid_from);
CREATE INDEX idx_profile_versions_user_current ON user_profile_versions(user_id, valid_until) 
    WHERE valid_until IS NULL;
```

**Design Notes:**
- `profile_snapshot` stores complete state for point-in-time recovery
- `valid_from` and `valid_until` enable temporal queries
- Supports "show me my plan from 3 weeks ago" feature requests

---

### 6.5 fitness_goals

**Purpose:** Detailed goal configuration with quantifiable targets

```sql
CREATE TABLE fitness_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Goal details
    goal_type VARCHAR(50) NOT NULL,
        -- Values: 'primary', 'secondary'
    goal_category VARCHAR(50) NOT NULL,
        -- Values: 'fat_loss', 'muscle_gain', 'general_fitness', 'strength', 
        --         'endurance', 'flexibility', 'athletic_performance'
    
    -- Target metrics (nullable, not all goals have numeric targets)
    target_weight_kg DECIMAL(5,2),
    target_body_fat_percentage DECIMAL(4,2),
    target_muscle_gain_kg DECIMAL(4,2),
    target_timeline_weeks INTEGER,
    
    -- Priority
    priority INTEGER NOT NULL DEFAULT 1,
        -- Lower number = higher priority
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active',
        -- Values: 'active', 'completed', 'paused', 'abandoned'
    
    -- Explanation from onboarding
    user_explanation TEXT,
        -- Why the user selected this goal
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_goal_type CHECK (goal_type IN ('primary', 'secondary')),
    CONSTRAINT valid_goal_status CHECK (
        status IN ('active', 'completed', 'paused', 'abandoned')
    ),
    CONSTRAINT valid_target_weight CHECK (
        target_weight_kg IS NULL OR (target_weight_kg > 0 AND target_weight_kg < 500)
    ),
    CONSTRAINT valid_body_fat CHECK (
        target_body_fat_percentage IS NULL OR 
        (target_body_fat_percentage >= 3 AND target_body_fat_percentage <= 50)
    )
);

CREATE INDEX idx_fitness_goals_user_id ON fitness_goals(user_id);
CREATE INDEX idx_fitness_goals_active ON fitness_goals(user_id, status) 
    WHERE status = 'active';
CREATE INDEX idx_fitness_goals_priority ON fitness_goals(user_id, priority);
```

---

### 6.6 physical_constraints

**Purpose:** Equipment, injuries, limitations, and preferences

```sql
CREATE TABLE physical_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Constraint type
    constraint_type VARCHAR(50) NOT NULL,
        -- Values: 'injury', 'limitation', 'equipment', 'location_preference', 'time_constraint'
    
    -- Details
    constraint_category VARCHAR(100),
        -- For injuries: 'knee', 'back', 'shoulder', etc.
        -- For equipment: 'dumbbells', 'barbell', 'resistance_bands', etc.
    description TEXT,
    
    -- Severity/Impact (for injuries and limitations)
    severity VARCHAR(50),
        -- Values: 'mild', 'moderate', 'severe' (nullable)
    
    -- Location preferences
    workout_location VARCHAR(50),
        -- Values: 'home', 'gym', 'outdoor', 'hybrid'
    
    -- Equipment availability (JSONB for flexible structure)
    available_equipment JSONB DEFAULT '[]'::jsonb,
        -- Array of equipment slugs: ["dumbbells", "bench", "pull_up_bar"]
    
    -- Time constraints
    max_workout_duration_minutes INTEGER,
    available_time_slots JSONB,
        -- Array of time ranges: [{"day": "monday", "start": "18:00", "end": "20:00"}]
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    resolved_at TIMESTAMP WITH TIME ZONE,
        -- For temporary injuries
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_constraint_type CHECK (
        constraint_type IN ('injury', 'limitation', 'equipment', 
                           'location_preference', 'time_constraint')
    ),
    CONSTRAINT valid_workout_location CHECK (
        workout_location IS NULL OR 
        workout_location IN ('home', 'gym', 'outdoor', 'hybrid')
    ),
    CONSTRAINT valid_max_duration CHECK (
        max_workout_duration_minutes IS NULL OR 
        (max_workout_duration_minutes >= 15 AND max_workout_duration_minutes <= 180)
    )
);

CREATE INDEX idx_physical_constraints_user_id ON physical_constraints(user_id);
CREATE INDEX idx_physical_constraints_active ON physical_constraints(user_id, is_active) 
    WHERE is_active = TRUE;
CREATE INDEX idx_physical_constraints_type ON physical_constraints(user_id, constraint_type);
CREATE INDEX idx_physical_constraints_equipment ON physical_constraints 
    USING GIN (available_equipment) WHERE constraint_type = 'equipment';
```

**Design Notes:**
- Flexible structure to handle multiple constraint types
- GIN index on JSONB for fast equipment availability queries
- `is_active` allows temporary constraints without deletion

---

### 6.7 dietary_preferences

**Purpose:** Diet type, restrictions, allergies, exclusions

```sql
CREATE TABLE dietary_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Primary diet type
    diet_type VARCHAR(50) NOT NULL,
        -- Values: 'omnivore', 'vegetarian', 'vegan', 'pescatarian', 
        --         'keto', 'paleo', 'mediterranean', 'other'
    diet_type_other VARCHAR(100),
        -- If diet_type = 'other'
    
    -- Restrictions and exclusions
    allergies TEXT[],
        -- Array: ['peanuts', 'shellfish', 'dairy']
    intolerances TEXT[],
        -- Array: ['lactose', 'gluten']
    dislikes TEXT[],
        -- Array: ['mushrooms', 'olives']
    religious_restrictions TEXT[],
        -- Array: ['pork', 'beef', 'alcohol']
    
    -- Preferences
    preferred_cuisines TEXT[],
        -- Array: ['italian', 'indian', 'mexican']
    cooking_skill_level VARCHAR(50),
        -- Values: 'beginner', 'intermediate', 'advanced'
    meal_prep_willingness VARCHAR(50),
        -- Values: 'none', 'minimal', 'moderate', 'extensive'
    
    -- Additional constraints
    max_meal_prep_time_minutes INTEGER,
    budget_per_day_usd DECIMAL(6,2),
    
    -- Free-form notes
    additional_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_diet_type CHECK (
        diet_type IN ('omnivore', 'vegetarian', 'vegan', 'pescatarian', 
                     'keto', 'paleo', 'mediterranean', 'other')
    ),
    CONSTRAINT valid_cooking_skill CHECK (
        cooking_skill_level IS NULL OR 
        cooking_skill_level IN ('beginner', 'intermediate', 'advanced')
    ),
    CONSTRAINT valid_meal_prep CHECK (
        meal_prep_willingness IS NULL OR 
        meal_prep_willingness IN ('none', 'minimal', 'moderate', 'extensive')
    )
);

CREATE UNIQUE INDEX idx_dietary_preferences_user_id ON dietary_preferences(user_id);
CREATE INDEX idx_dietary_preferences_diet_type ON dietary_preferences(diet_type);
```

---

### 6.8 meal_plans

**Purpose:** Fixed nutritional structure (locked configuration)

```sql
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Plan structure
    meals_per_day INTEGER NOT NULL,
        -- Typical: 3, 4, 5, or 6
    
    -- Caloric targets
    daily_calories_target INTEGER NOT NULL,
    daily_calories_min INTEGER NOT NULL,
    daily_calories_max INTEGER NOT NULL,
    
    -- Macronutrient targets (grams)
    protein_grams_target DECIMAL(6,2) NOT NULL,
    carbs_grams_target DECIMAL(6,2) NOT NULL,
    fats_grams_target DECIMAL(6,2) NOT NULL,
    
    -- Macro percentages (for validation)
    protein_percentage DECIMAL(4,2),
    carbs_percentage DECIMAL(4,2),
    fats_percentage DECIMAL(4,2),
    
    -- Rationale
    plan_rationale TEXT,
        -- AI-generated explanation of why this plan fits user goals
    
    -- Lock status
    is_locked BOOLEAN DEFAULT TRUE,
    locked_at TIMESTAMP WITH TIME ZONE,
    
    -- Recalculation tracking
    last_recalculated_at TIMESTAMP WITH TIME ZONE,
    recalculation_reason TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_meals_per_day CHECK (meals_per_day >= 2 AND meals_per_day <= 8),
    CONSTRAINT valid_calories CHECK (
        daily_calories_target >= 1000 AND 
        daily_calories_target <= 5000 AND
        daily_calories_min < daily_calories_target AND
        daily_calories_target < daily_calories_max
    ),
    CONSTRAINT valid_macros CHECK (
        protein_grams_target > 0 AND
        carbs_grams_target > 0 AND
        fats_grams_target > 0
    ),
    CONSTRAINT valid_macro_percentages CHECK (
        protein_percentage + carbs_percentage + fats_percentage = 100
    )
);

CREATE UNIQUE INDEX idx_meal_plans_user_id ON meal_plans(user_id);
CREATE INDEX idx_meal_plans_updated ON meal_plans(updated_at DESC);
```

**Design Notes:**
- Stores target ranges, not absolute values (allows flexibility)
- `plan_rationale` enables explainability
- Separate min/max provides buffer for daily adjustments

---

### 6.9 meal_schedules

**Purpose:** Timing for each meal (enables notifications and contextual assistance)

```sql
CREATE TABLE meal_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
    
    -- Meal identification
    meal_number INTEGER NOT NULL,
        -- 1 = breakfast, 2 = lunch, etc.
    meal_name VARCHAR(50),
        -- User-friendly: 'Breakfast', 'Morning Snack', 'Lunch', etc.
    
    -- Timing
    scheduled_time TIME NOT NULL,
        -- Time of day (no timezone - interpreted in user's local time)
    notification_offset_minutes INTEGER DEFAULT -15,
        -- Notify X minutes before meal time
    
    -- Flexibility window
    earliest_time TIME,
    latest_time TIME,
        -- Acceptable eating window
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_meal_number CHECK (meal_number >= 1 AND meal_number <= 10),
    CONSTRAINT valid_notification_offset CHECK (
        notification_offset_minutes >= -120 AND 
        notification_offset_minutes <= 0
    ),
    CONSTRAINT unique_user_meal_number UNIQUE(user_id, meal_number)
);

CREATE INDEX idx_meal_schedules_user_id ON meal_schedules(user_id);
CREATE INDEX idx_meal_schedules_meal_plan ON meal_schedules(meal_plan_id);
CREATE INDEX idx_meal_schedules_time ON meal_schedules(user_id, scheduled_time);
```

---

### 6.10 workout_schedules

**Purpose:** Workout days, timing, and rest days

```sql
CREATE TABLE workout_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Weekly pattern
    monday_workout BOOLEAN DEFAULT FALSE,
    tuesday_workout BOOLEAN DEFAULT FALSE,
    wednesday_workout BOOLEAN DEFAULT FALSE,
    thursday_workout BOOLEAN DEFAULT FALSE,
    friday_workout BOOLEAN DEFAULT FALSE,
    saturday_workout BOOLEAN DEFAULT FALSE,
    sunday_workout BOOLEAN DEFAULT FALSE,
    
    -- Preferred workout time
    preferred_workout_time TIME,
    preferred_workout_duration_minutes INTEGER,
    
    -- Notifications
    workout_reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_offset_minutes INTEGER DEFAULT -30,
    
    -- Rest day handling
    rest_day_preference VARCHAR(50),
        -- Values: 'fixed', 'flexible', 'auto'
    
    -- Lock status
    is_locked BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_duration CHECK (
        preferred_workout_duration_minutes IS NULL OR
        (preferred_workout_duration_minutes >= 15 AND 
         preferred_workout_duration_minutes <= 180)
    ),
    CONSTRAINT at_least_one_workout_day CHECK (
        monday_workout OR tuesday_workout OR wednesday_workout OR 
        thursday_workout OR friday_workout OR saturday_workout OR sunday_workout
    ),
    CONSTRAINT unique_user_schedule UNIQUE(user_id)
);

CREATE UNIQUE INDEX idx_workout_schedules_user_id ON workout_schedules(user_id);
```

**Design Notes:**
- Boolean columns for each day enable simple querying
- Alternative design: separate rows per day (more normalized, but slower queries)
- Current design optimized for "what's my schedule this week" queries

---

### 6.11 hydration_preferences

**Purpose:** Water intake reminders and tracking preferences

```sql
CREATE TABLE hydration_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Target intake
    daily_water_target_ml INTEGER NOT NULL DEFAULT 2000,
    
    -- Reminder settings
    reminder_enabled BOOLEAN DEFAULT TRUE,
    reminder_frequency_minutes INTEGER DEFAULT 60,
        -- How often to remind
    
    -- Reminder time window
    reminder_start_time TIME DEFAULT '08:00',
    reminder_end_time TIME DEFAULT '22:00',
        -- Don't send reminders outside this window
    
    -- Reminder style
    reminder_tone VARCHAR(50) DEFAULT 'gentle',
        -- Values: 'gentle', 'motivational', 'minimal'
    
    -- Integration with meals
    auto_remind_with_meals BOOLEAN DEFAULT TRUE,
        -- Remind to drink water with each meal
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_water_target CHECK (
        daily_water_target_ml >= 500 AND daily_water_target_ml <= 10000
    ),
    CONSTRAINT valid_frequency CHECK (
        reminder_frequency_minutes >= 15 AND reminder_frequency_minutes <= 480
    ),
    CONSTRAINT valid_reminder_tone CHECK (
        reminder_tone IN ('gentle', 'motivational', 'minimal')
    )
);

CREATE UNIQUE INDEX idx_hydration_preferences_user_id ON hydration_preferences(user_id);
```

---

### 6.12 lifestyle_baselines

**Purpose:** Energy, stress, sleep tracking over time (enables trend analysis)

```sql
CREATE TABLE lifestyle_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Current state
    energy_level VARCHAR(50) NOT NULL,
        -- Values: 'low', 'medium', 'high'
    stress_level VARCHAR(50) NOT NULL,
        -- Values: 'low', 'medium', 'high'
    sleep_quality VARCHAR(50) NOT NULL,
        -- Values: 'poor', 'fair', 'good', 'excellent'
    
    -- Additional context
    sleep_hours_last_night DECIMAL(3,1),
    sleep_quality_notes TEXT,
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Source
    data_source VARCHAR(50) DEFAULT 'user_input',
        -- Values: 'user_input', 'wearable', 'system'
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_energy_level CHECK (
        energy_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT valid_stress_level CHECK (
        stress_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT valid_sleep_quality CHECK (
        sleep_quality IN ('poor', 'fair', 'good', 'excellent')
    ),
    CONSTRAINT valid_sleep_hours CHECK (
        sleep_hours_last_night IS NULL OR 
        (sleep_hours_last_night >= 0 AND sleep_hours_last_night <= 24)
    )
);

CREATE INDEX idx_lifestyle_baselines_user_id ON lifestyle_baselines(user_id, recorded_at DESC);
CREATE INDEX idx_lifestyle_baselines_recent ON lifestyle_baselines(user_id) 
    WHERE recorded_at > CURRENT_TIMESTAMP - INTERVAL '30 days';
```

**Design Notes:**
- Time-series data (multiple rows per user)
- Enables trend analysis: "User's sleep quality deteriorating over past 2 weeks"
- Recent data index optimizes dashboard queries

---

### 6.13 Reference/Lookup Tables

```sql
-- Fitness experience levels
CREATE TABLE ref_fitness_levels (
    code VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL
);

INSERT INTO ref_fitness_levels (code, display_name, description, sort_order) VALUES
('beginner', 'Beginner', 'New to fitness or returning after long break', 1),
('intermediate', 'Intermediate', 'Consistent training for 6+ months', 2),
('advanced', 'Advanced', 'Years of training experience', 3);

-- Goal categories
CREATE TABLE ref_goal_categories (
    code VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    compatible_with_primary BOOLEAN DEFAULT TRUE,
    compatible_with_secondary BOOLEAN DEFAULT TRUE
);

-- Diet types
CREATE TABLE ref_diet_types (
    code VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    excludes_food_groups TEXT[]
);

-- Equipment types
CREATE TABLE ref_equipment_types (
    code VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    typical_locations TEXT[]
);
```

---

## 7. Indexes and Performance

### Primary Indexes (Already Defined Above)
All foreign keys have indexes automatically created.

### Composite Indexes for Common Queries

```sql
-- User profile retrieval with all related data (most common query)
CREATE INDEX idx_user_complete_profile ON user_profiles(user_id, is_locked);

-- Onboarding analytics: incomplete users by start date
CREATE INDEX idx_onboarding_analytics ON onboarding_states(
    completed_at, 
    started_at DESC
) WHERE completed_at IS NULL;

-- AI agent context loading: active goals + constraints
CREATE INDEX idx_active_user_context ON fitness_goals(user_id, status, priority)
    WHERE status = 'active';

-- Recent lifestyle trends (last 30 days)
CREATE INDEX idx_lifestyle_trends ON lifestyle_baselines(
    user_id, 
    recorded_at DESC
) WHERE recorded_at > CURRENT_TIMESTAMP - INTERVAL '30 days';
```

### Performance Targets
| Query Type | Target Latency | Notes |
|------------|----------------|-------|
| Get user profile | < 50ms | Single user lookup with joins |
| Load onboarding state | < 30ms | Single table, indexed |
| Get complete AI context | < 100ms | Profile + goals + constraints |
| Save onboarding step | < 200ms | Includes transaction + version creation |
| Recent lifestyle data (30d) | < 80ms | Partial index optimization |

---

## 8. Data Validation Rules

### Application-Layer Validation
These validations should happen BEFORE database insertion:

1. **Email Format**: RFC 5322 compliant
2. **Time Ranges**: Ensure `earliest_time < scheduled_time < latest_time`
3. **Calorie Calculations**: Validate macros sum to target calories (±50 cal tolerance)
4. **Schedule Conflicts**: No overlapping meal times
5. **Equipment Availability**: Cross-reference with `ref_equipment_types`
6. **Goal Compatibility**: Primary and secondary goals must be compatible

### Database Constraints
Already defined in table schemas via `CHECK` constraints.

### Referential Integrity
- All foreign keys use `ON DELETE CASCADE` for clean user deletion
- Soft deletes via `deleted_at` timestamp where historical data needed
- Version tables use `ON DELETE RESTRICT` to prevent orphaned history

---

## 9. Migration Strategy

### Initial Deployment
```sql
-- Migration 001: Core user tables
-- Migration 002: Profile and preferences
-- Migration 003: Schedules and plans
-- Migration 004: Indexes and constraints
-- Migration 005: Reference data
```

### Version Control
- Use Flyway or Liquibase for migration management
- All migrations must be idempotent
- Include rollback scripts for each migration
- Test migrations on staging with production-sized data

### Data Migration from Older Versions
If onboarding flow changes:
1. Update `onboarding_states.flow_version`
2. Create migration script to backfill new required fields with sensible defaults
3. Flag affected users for re-onboarding if critical data missing

---

## 10. API Considerations

### Read Endpoints (GET)
```
GET /api/v1/users/{userId}/profile
    - Returns: Complete user profile + all related preferences
    - Cache: 24h
    - Authorization: User or Admin

GET /api/v1/users/{userId}/onboarding/state
    - Returns: Current onboarding progress
    - Cache: 5m
    - Authorization: User only

GET /api/v1/users/{userId}/profile/history
    - Returns: List of profile versions
    - Cache: 1h
    - Authorization: User only
```

### Write Endpoints (POST/PUT/PATCH)
```
POST /api/v1/onboarding/step
    - Saves single onboarding step
    - Validates: Step sequence, data format
    - Returns: Updated state + next step info

PUT /api/v1/users/{userId}/profile/lock
    - Locks profile after onboarding confirmation
    - Creates initial profile version
    - Returns: Success + locked profile

PATCH /api/v1/users/{userId}/profile
    - Unlocks, updates, and re-locks profile
    - Creates new version in history
    - Requires: modification_reason field
    - Authorization: User + unlock verification
```

### Bulk/Admin Endpoints
```
GET /api/v1/admin/onboarding/incomplete
    - Returns: List of users with incomplete onboarding
    - Pagination required
    - Authorization: Admin only

POST /api/v1/admin/users/{userId}/reset-onboarding
    - Resets onboarding state
    - Archives current profile
    - Authorization: Admin + user consent
```

---

## 11. Security & Privacy

### Data Encryption
- **At Rest**: AES-256 encryption for database volumes
- **In Transit**: TLS 1.3 for all API communication
- **PII Fields**: Consider field-level encryption for:
  - `users.email`
  - `dietary_preferences.additional_notes`
  - `physical_constraints.description`

### Access Control
- Row-Level Security (RLS) policies in PostgreSQL:
  ```sql
  ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
  
  CREATE POLICY user_profiles_select_policy ON user_profiles
      FOR SELECT
      USING (user_id = current_setting('app.current_user_id')::uuid);
  ```

### GDPR Compliance

#### Right to Access
Query all user data:
```sql
SELECT * FROM users WHERE id = ?
UNION ALL
SELECT * FROM user_profiles WHERE user_id = ?
-- ... (all related tables)
```

#### Right to Erasure
```sql
-- Anonymization strategy (preferred over hard delete)
UPDATE users 
SET 
    email = 'deleted_' || id || '@anonymized.local',
    external_auth_id = 'deleted_' || id,
    account_status = 'deleted',
    deleted_at = CURRENT_TIMESTAMP,
    metadata = '{}'::jsonb
WHERE id = ?;

-- Cascade soft-deletes to all related tables
UPDATE user_profiles SET updated_at = CURRENT_TIMESTAMP WHERE user_id = ?;
-- ... (trigger handles soft delete propagation)
```

#### Data Retention
- Active users: Indefinite
- Inactive users (no login > 2 years): Soft delete notification
- Deleted users: Hard delete after 90 days (compliance requirement)

### Audit Logging
Track all modifications:
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 12. Monitoring & Observability

### Key Metrics to Track
1. **Onboarding Funnel**:
   - Completion rate per step
   - Average time per step
   - Drop-off points
   
2. **Database Performance**:
   - Query latency (p50, p95, p99)
   - Connection pool utilization
   - Cache hit rates
   
3. **Data Quality**:
   - NULL field percentages
   - Constraint violation attempts
   - Profile version churn rate

### Alerting Thresholds
- Onboarding completion rate < 60% (trailing 7 days)
- Query latency p95 > 200ms
- Failed profile updates > 1% of attempts
- Disk usage > 80%

---

## Appendix A: Sample Queries

### Get Complete User Context for AI Agents
```sql
SELECT 
    u.id as user_id,
    up.fitness_level,
    up.primary_goal,
    up.secondary_goal,
    up.energy_level,
    up.stress_level,
    up.sleep_quality,
    json_agg(DISTINCT fg.*) as fitness_goals,
    json_agg(DISTINCT pc.*) as constraints,
    json_agg(DISTINCT dp.*) as dietary_prefs,
    mp.* as meal_plan,
    json_agg(DISTINCT ms.*) as meal_schedule,
    ws.* as workout_schedule
FROM users u
JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN fitness_goals fg ON u.id = fg.user_id AND fg.status = 'active'
LEFT JOIN physical_constraints pc ON u.id = pc.user_id AND pc.is_active = TRUE
LEFT JOIN dietary_preferences dp ON u.id = dp.user_id
LEFT JOIN meal_plans mp ON u.id = mp.user_id
LEFT JOIN meal_schedules ms ON u.id = ms.user_id
LEFT JOIN workout_schedules ws ON u.id = ws.user_id
WHERE u.id = ? AND u.deleted_at IS NULL
GROUP BY u.id, up.id, mp.id, ws.id;
```

### Onboarding Analytics
```sql
SELECT 
    DATE_TRUNC('day', started_at) as date,
    COUNT(*) as started,
    COUNT(completed_at) as completed,
    ROUND(COUNT(completed_at)::numeric / COUNT(*)::numeric * 100, 2) as completion_rate_pct,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/60) as avg_completion_time_minutes
FROM onboarding_states
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY date DESC;
```

---

## Appendix B: Schema Evolution

### Planned Enhancements (Future Versions)

**v1.1**: Add wearable integration
- New table: `wearable_connections`
- Fields: `device_type`, `last_sync_at`, `sync_status`

**v1.2**: Social features
- New table: `user_connections` (friends/coaches)
- New table: `shared_workouts`

**v1.3**: Progress tracking
- New table: `body_measurements` (weight, body fat %, photos)
- New table: `workout_logs`
- New table: `meal_logs`

**v2.0**: Multi-goal support
- Modify `fitness_goals` to allow multiple active primary goals
- Add goal priority weighting system

---

## Appendix C: Disaster Recovery

### Backup Strategy
- **Full backups**: Daily at 02:00 UTC
- **Incremental backups**: Every 6 hours
- **Transaction log backups**: Every 15 minutes
- **Retention**: 30 days for production, 7 days for staging

### Recovery Procedures
1. **Point-in-Time Recovery**: 15-minute granularity
2. **Table-Level Restore**: Via `pg_restore --table`
3. **User-Level Restore**: Query backups for specific `user_id`

### RTO/RPO Targets
- **Recovery Time Objective (RTO)**: < 4 hours
- **Recovery Point Objective (RPO)**: < 15 minutes

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-28 | Engineering Team | Initial schema design |

---

## Approval

**Technical Review:**
- [ ] Backend Lead Engineer
- [ ] Database Administrator
- [ ] Security Team

**Product Review:**
- [ ] Product Manager
- [ ] AI/ML Team Lead

**Compliance Review:**
- [ ] Legal Team (GDPR/Privacy)

---

**End of Document**