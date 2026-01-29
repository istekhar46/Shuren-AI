# Design Document: Phase 1 Foundation

## Overview

Phase 1 establishes the foundational infrastructure for the Shuren AI fitness application backend. This phase implements a FastAPI-based REST API with PostgreSQL database, JWT authentication (including Google OAuth), and a comprehensive onboarding system. The design follows a layered architecture pattern with clear separation between API, service, and data layers.

### Key Design Goals

1. **Async-First Architecture**: All I/O operations use async/await for optimal performance
2. **Type Safety**: Pydantic schemas for validation, SQLAlchemy models for database
3. **Maintainability**: Clear separation of concerns across layers
4. **Performance**: Sub-100ms profile queries through proper indexing
5. **Auditability**: Immutable version history for all profile changes
6. **Security**: JWT tokens, bcrypt password hashing, OAuth2 integration

### Technology Stack

- **Framework**: FastAPI 0.109+ (Python 3.11+)
- **Database**: PostgreSQL 15+ with asyncpg driver
- **ORM**: SQLAlchemy 2.0+ (async)
- **Validation**: Pydantic 2.0+
- **Authentication**: python-jose (JWT), Google OAuth2
- **Password Hashing**: bcrypt
- **Migrations**: Alembic
- **ASGI Server**: Uvicorn

## Architecture

### Layered Architecture Pattern

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│  - Request validation (Pydantic)        │
│  - Response serialization               │
│  - Dependency injection                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer                   │
│  - Business logic                       │
│  - Orchestration                        │
│  - Transaction management               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer (SQLAlchemy)         │
│  - ORM models                           │
│  - Database queries                     │
│  - Relationships                        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PostgreSQL Database             │
└─────────────────────────────────────────┘
```

### Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Pydantic settings configuration
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── onboarding.py  # Onboarding flow
│   │           └── profiles.py    # Profile management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── onboarding.py
│   │   ├── profile.py
│   │   └── preferences.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── profile.py
│   │   └── preferences.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── onboarding_service.py
│   │   └── profile_service.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── deps.py          # Dependency injection
│   └── db/
│       ├── __init__.py
│       ├── base.py
│       └── session.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
├── requirements.txt
├── .env.example
└── README.md
```

## Components and Interfaces

### 1. Configuration Management (app/core/config.py)

**Purpose**: Centralized configuration using Pydantic BaseSettings

**Interface**:
```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Shuren Backend"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Design Decisions**:
- Use Pydantic for automatic validation and type conversion
- Load from .env file for local development
- Environment variables override .env values for production
- Sensitive values (secrets) never have defaults

### 2. Database Session Management (app/db/session.py)

**Purpose**: Async database session factory and dependency injection

**Interface**:
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Design Decisions**:
- Use asyncpg driver for PostgreSQL (postgresql+asyncpg://)
- expire_on_commit=False to avoid additional queries after commit
- Context manager ensures proper session cleanup
- FastAPI dependency injection for automatic session management

### 3. Base Model (app/db/base.py)

**Purpose**: Base class for all SQLAlchemy models with common fields

**Interface**:
```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

**Design Decisions**:
- UUID primary keys for distributed system compatibility
- Automatic timestamp management via server_default and onupdate
- Soft delete support via deleted_at column
- UTC timestamps enforced at database level

### 4. Authentication Service (app/core/security.py)

**Purpose**: JWT token generation, password hashing, OAuth validation

**Interface**:
```python
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

async def verify_google_token(token: str) -> dict:
    # Validate Google ID token using Google's token verification endpoint
    # Returns user info: email, name, sub (Google user ID)
    pass
```

**Design Decisions**:
- bcrypt with default cost factor (12) for password hashing
- JWT tokens with HS256 algorithm (symmetric signing)
- Token payload includes user_id and expiration
- Google OAuth uses official Google token verification library
- No refresh tokens in Phase 1 (24-hour expiration sufficient)

### 5. Authentication Dependencies (app/core/deps.py)

**Purpose**: FastAPI dependencies for authentication and authorization

**Interface**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

**Design Decisions**:
- Use HTTPBearer for automatic Authorization header parsing
- Validate token and fetch user in single dependency
- Check for soft-deleted users
- Raise 401 for authentication failures

### 6. Onboarding Service (app/services/onboarding_service.py)

**Purpose**: Business logic for onboarding flow management

**Interface**:
```python
class OnboardingService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_onboarding_state(self, user_id: UUID) -> OnboardingState:
        # Retrieve current onboarding state
        pass
    
    async def save_onboarding_step(
        self, 
        user_id: UUID, 
        step: int, 
        data: dict
    ) -> OnboardingState:
        # Validate step data, save to appropriate tables, advance state
        pass
    
    async def complete_onboarding(self, user_id: UUID) -> UserProfile:
        # Create locked user profile from onboarding data
        # Create initial profile version
        pass
```

**Design Decisions**:
- Service layer handles transaction boundaries
- Step validation logic centralized in service
- Atomic operations for state transitions
- Profile creation happens only after all steps complete

### 7. Profile Service (app/services/profile_service.py)

**Purpose**: Business logic for profile management and versioning

**Interface**:
```python
class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile(self, user_id: UUID) -> UserProfile:
        # Retrieve profile with all related entities
        # Use eager loading for performance
        pass
    
    async def update_profile(
        self, 
        user_id: UUID, 
        updates: dict,
        reason: str
    ) -> UserProfile:
        # Check if profile is locked
        # Create new profile version
        # Apply updates
        pass
    
    async def lock_profile(self, user_id: UUID) -> UserProfile:
        # Set is_locked = True
        pass
```

**Design Decisions**:
- Eager loading for related entities to minimize queries
- Profile versions created before any modification
- Lock status checked before updates
- Reason required for all profile modifications

## Data Models

### Core Database Schema

#### 1. users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),  -- Nullable for OAuth users
    full_name VARCHAR(255) NOT NULL,
    oauth_provider VARCHAR(50),     -- 'google', NULL for email/password
    oauth_provider_user_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_oauth_user UNIQUE (oauth_provider, oauth_provider_user_id)
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_provider_user_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    oauth_provider = Column(String(50), nullable=True)
    oauth_provider_user_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    onboarding_state = relationship("OnboardingState", back_populates="user", uselist=False)
    profile = relationship("UserProfile", back_populates="user", uselist=False)
```

#### 2. onboarding_states Table

```sql
CREATE TABLE onboarding_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    current_step INTEGER DEFAULT 0,
    is_complete BOOLEAN DEFAULT FALSE,
    step_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_user_onboarding UNIQUE (user_id)
);

CREATE INDEX idx_onboarding_user ON onboarding_states(user_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class OnboardingState(BaseModel):
    __tablename__ = "onboarding_states"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    current_step = Column(Integer, default=0)
    is_complete = Column(Boolean, default=False)
    step_data = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="onboarding_state")
```

#### 3. user_profiles Table

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    is_locked BOOLEAN DEFAULT FALSE,
    fitness_level VARCHAR(50),  -- 'beginner', 'intermediate', 'advanced'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_user_profile UNIQUE (user_id)
);

CREATE INDEX idx_profile_user ON user_profiles(user_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class UserProfile(BaseModel):
    __tablename__ = "user_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    is_locked = Column(Boolean, default=False)
    fitness_level = Column(String(50))
    
    # Relationships
    user = relationship("User", back_populates="profile")
    versions = relationship("UserProfileVersion", back_populates="profile")
    fitness_goals = relationship("FitnessGoal", back_populates="profile")
    physical_constraints = relationship("PhysicalConstraint", back_populates="profile")
    dietary_preferences = relationship("DietaryPreference", back_populates="profile")
    meal_plan = relationship("MealPlan", back_populates="profile", uselist=False)
    meal_schedules = relationship("MealSchedule", back_populates="profile")
    workout_schedules = relationship("WorkoutSchedule", back_populates="profile")
    hydration_preferences = relationship("HydrationPreference", back_populates="profile", uselist=False)
    lifestyle_baseline = relationship("LifestyleBaseline", back_populates="profile", uselist=False)
```

#### 4. user_profile_versions Table

```sql
CREATE TABLE user_profile_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    version_number INTEGER NOT NULL,
    change_reason VARCHAR(500),
    snapshot JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_profile_versions ON user_profile_versions(profile_id, version_number);
```

**SQLAlchemy Model**:
```python
class UserProfileVersion(BaseModel):
    __tablename__ = "user_profile_versions"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_reason = Column(String(500))
    snapshot = Column(JSONB, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="versions")
```

#### 5. fitness_goals Table

```sql
CREATE TABLE fitness_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    goal_type VARCHAR(50) NOT NULL,  -- 'fat_loss', 'muscle_gain', 'general_fitness'
    target_weight_kg DECIMAL(5,2),
    target_body_fat_percentage DECIMAL(4,2),
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_fitness_goals_profile ON fitness_goals(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class FitnessGoal(BaseModel):
    __tablename__ = "fitness_goals"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    goal_type = Column(String(50), nullable=False)
    target_weight_kg = Column(Numeric(5, 2))
    target_body_fat_percentage = Column(Numeric(4, 2))
    priority = Column(Integer, default=1)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="fitness_goals")
```

#### 6. physical_constraints Table

```sql
CREATE TABLE physical_constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    constraint_type VARCHAR(50) NOT NULL,  -- 'equipment', 'injury', 'limitation'
    description TEXT NOT NULL,
    severity VARCHAR(20),  -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_physical_constraints_profile ON physical_constraints(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class PhysicalConstraint(BaseModel):
    __tablename__ = "physical_constraints"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    constraint_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20))
    
    # Relationships
    profile = relationship("UserProfile", back_populates="physical_constraints")
```

#### 7. dietary_preferences Table

```sql
CREATE TABLE dietary_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    diet_type VARCHAR(50) NOT NULL,  -- 'omnivore', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo'
    allergies TEXT[],
    intolerances TEXT[],
    dislikes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_profile_dietary UNIQUE (profile_id)
);

CREATE INDEX idx_dietary_preferences_profile ON dietary_preferences(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
from sqlalchemy.dialects.postgresql import ARRAY

class DietaryPreference(BaseModel):
    __tablename__ = "dietary_preferences"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    diet_type = Column(String(50), nullable=False)
    allergies = Column(ARRAY(Text), default=[])
    intolerances = Column(ARRAY(Text), default=[])
    dislikes = Column(ARRAY(Text), default=[])
    
    # Relationships
    profile = relationship("UserProfile", back_populates="dietary_preferences")
```

#### 8. meal_plans Table

```sql
CREATE TABLE meal_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    daily_calorie_target INTEGER NOT NULL,
    protein_percentage DECIMAL(5,2) NOT NULL,
    carbs_percentage DECIMAL(5,2) NOT NULL,
    fats_percentage DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_profile_meal_plan UNIQUE (profile_id),
    CONSTRAINT valid_macro_sum CHECK (protein_percentage + carbs_percentage + fats_percentage = 100)
);

CREATE INDEX idx_meal_plans_profile ON meal_plans(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class MealPlan(BaseModel):
    __tablename__ = "meal_plans"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    daily_calorie_target = Column(Integer, nullable=False)
    protein_percentage = Column(Numeric(5, 2), nullable=False)
    carbs_percentage = Column(Numeric(5, 2), nullable=False)
    fats_percentage = Column(Numeric(5, 2), nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_plan")
```

#### 9. meal_schedules Table

```sql
CREATE TABLE meal_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    meal_name VARCHAR(100) NOT NULL,  -- 'breakfast', 'lunch', 'dinner', 'snack_1', etc.
    scheduled_time TIME NOT NULL,
    enable_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_meal_schedules_profile ON meal_schedules(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class MealSchedule(BaseModel):
    __tablename__ = "meal_schedules"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    meal_name = Column(String(100), nullable=False)
    scheduled_time = Column(Time, nullable=False)
    enable_notifications = Column(Boolean, default=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_schedules")
```

#### 10. workout_schedules Table

```sql
CREATE TABLE workout_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    day_of_week INTEGER NOT NULL,  -- 0=Monday, 6=Sunday
    scheduled_time TIME NOT NULL,
    enable_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workout_schedules_profile ON workout_schedules(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class WorkoutSchedule(BaseModel):
    __tablename__ = "workout_schedules"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    enable_notifications = Column(Boolean, default=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="workout_schedules")
```

#### 11. hydration_preferences Table

```sql
CREATE TABLE hydration_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    daily_water_target_ml INTEGER NOT NULL,
    reminder_frequency_minutes INTEGER DEFAULT 60,
    enable_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_profile_hydration UNIQUE (profile_id)
);

CREATE INDEX idx_hydration_preferences_profile ON hydration_preferences(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class HydrationPreference(BaseModel):
    __tablename__ = "hydration_preferences"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    daily_water_target_ml = Column(Integer, nullable=False)
    reminder_frequency_minutes = Column(Integer, default=60)
    enable_notifications = Column(Boolean, default=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="hydration_preferences")
```

#### 12. lifestyle_baselines Table

```sql
CREATE TABLE lifestyle_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES user_profiles(id),
    energy_level INTEGER CHECK (energy_level BETWEEN 1 AND 10),
    stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    sleep_quality INTEGER CHECK (sleep_quality BETWEEN 1 AND 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_profile_lifestyle UNIQUE (profile_id)
);

CREATE INDEX idx_lifestyle_baselines_profile ON lifestyle_baselines(profile_id) WHERE deleted_at IS NULL;
```

**SQLAlchemy Model**:
```python
class LifestyleBaseline(BaseModel):
    __tablename__ = "lifestyle_baselines"
    
    profile_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False, unique=True)
    energy_level = Column(Integer)
    stress_level = Column(Integer)
    sleep_quality = Column(Integer)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="lifestyle_baseline")
```

### Pydantic Schemas

#### Authentication Schemas (app/schemas/auth.py)

```python
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    oauth_provider: str | None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Onboarding Schemas (app/schemas/onboarding.py)

```python
from pydantic import BaseModel
from typing import Any

class OnboardingStateResponse(BaseModel):
    id: str
    user_id: str
    current_step: int
    is_complete: bool
    step_data: dict[str, Any]
    
    class Config:
        from_attributes = True

class OnboardingStepRequest(BaseModel):
    step: int
    data: dict[str, Any]

class OnboardingStepResponse(BaseModel):
    current_step: int
    is_complete: bool
    message: str
```

#### Profile Schemas (app/schemas/profile.py)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time

class FitnessGoalSchema(BaseModel):
    goal_type: str
    target_weight_kg: Optional[float] = None
    target_body_fat_percentage: Optional[float] = None
    priority: int = 1

class PhysicalConstraintSchema(BaseModel):
    constraint_type: str
    description: str
    severity: Optional[str] = None

class DietaryPreferenceSchema(BaseModel):
    diet_type: str
    allergies: List[str] = []
    intolerances: List[str] = []
    dislikes: List[str] = []

class MealPlanSchema(BaseModel):
    daily_calorie_target: int
    protein_percentage: float
    carbs_percentage: float
    fats_percentage: float

class MealScheduleSchema(BaseModel):
    meal_name: str
    scheduled_time: time
    enable_notifications: bool = True

class WorkoutScheduleSchema(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    scheduled_time: time
    enable_notifications: bool = True

class HydrationPreferenceSchema(BaseModel):
    daily_water_target_ml: int
    reminder_frequency_minutes: int = 60
    enable_notifications: bool = True

class LifestyleBaselineSchema(BaseModel):
    energy_level: int = Field(..., ge=1, le=10)
    stress_level: int = Field(..., ge=1, le=10)
    sleep_quality: int = Field(..., ge=1, le=10)

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    is_locked: bool
    fitness_level: str
    fitness_goals: List[FitnessGoalSchema]
    physical_constraints: List[PhysicalConstraintSchema]
    dietary_preferences: Optional[DietaryPreferenceSchema]
    meal_plan: Optional[MealPlanSchema]
    meal_schedules: List[MealScheduleSchema]
    workout_schedules: List[WorkoutScheduleSchema]
    hydration_preferences: Optional[HydrationPreferenceSchema]
    lifestyle_baseline: Optional[LifestyleBaselineSchema]
    
    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    updates: dict[str, Any]
```

### API Endpoints

#### Authentication Endpoints (app/api/v1/endpoints/auth.py)

**POST /api/v1/auth/register**
- Request: `UserRegister`
- Response: `TokenResponse`
- Status: 201 Created
- Errors: 400 (email exists), 422 (validation)

**POST /api/v1/auth/login**
- Request: `UserLogin`
- Response: `TokenResponse`
- Status: 200 OK
- Errors: 401 (invalid credentials), 422 (validation)

**POST /api/v1/auth/google**
- Request: `GoogleAuthRequest`
- Response: `TokenResponse`
- Status: 200 OK
- Errors: 401 (invalid token), 422 (validation)

**GET /api/v1/auth/me**
- Headers: Authorization: Bearer {token}
- Response: `UserResponse`
- Status: 200 OK
- Errors: 401 (unauthorized)

#### Onboarding Endpoints (app/api/v1/endpoints/onboarding.py)

**GET /api/v1/onboarding/state**
- Headers: Authorization: Bearer {token}
- Response: `OnboardingStateResponse`
- Status: 200 OK
- Errors: 401 (unauthorized), 404 (state not found)

**POST /api/v1/onboarding/step**
- Headers: Authorization: Bearer {token}
- Request: `OnboardingStepRequest`
- Response: `OnboardingStepResponse`
- Status: 200 OK
- Errors: 401 (unauthorized), 400 (invalid step), 422 (validation)

**POST /api/v1/onboarding/complete**
- Headers: Authorization: Bearer {token}
- Response: `UserProfileResponse`
- Status: 201 Created
- Errors: 401 (unauthorized), 400 (onboarding incomplete)

#### Profile Endpoints (app/api/v1/endpoints/profiles.py)

**GET /api/v1/profiles/me**
- Headers: Authorization: Bearer {token}
- Response: `UserProfileResponse`
- Status: 200 OK
- Errors: 401 (unauthorized), 404 (profile not found)

**PATCH /api/v1/profiles/me**
- Headers: Authorization: Bearer {token}
- Request: `ProfileUpdateRequest`
- Response: `UserProfileResponse`
- Status: 200 OK
- Errors: 401 (unauthorized), 403 (profile locked), 422 (validation)

**POST /api/v1/profiles/me/lock**
- Headers: Authorization: Bearer {token}
- Response: `UserProfileResponse`
- Status: 200 OK
- Errors: 401 (unauthorized), 404 (profile not found)

### Authentication Flow Diagrams

#### Email/Password Registration Flow

```
Client                    API                     Database
  |                        |                          |
  |--POST /auth/register-->|                          |
  |  {email, password,     |                          |
  |   full_name}           |                          |
  |                        |--Check email exists----->|
  |                        |<-------Result------------|
  |                        |                          |
  |                        |--Hash password---------->|
  |                        |                          |
  |                        |--Create user------------>|
  |                        |<-------User--------------|
  |                        |                          |
  |                        |--Create onboarding------>|
  |                        |   state (step 0)         |
  |                        |<-------State-------------|
  |                        |                          |
  |                        |--Generate JWT token----->|
  |                        |                          |
  |<--201 {access_token}---|                          |
  |                        |                          |
```

#### Google OAuth Flow

```
Client                    API                     Google              Database
  |                        |                          |                   |
  |--POST /auth/google---->|                          |                   |
  |  {id_token}            |                          |                   |
  |                        |--Verify token----------->|                   |
  |                        |<--User info (email,------|                   |
  |                        |   name, sub)             |                   |
  |                        |                          |                   |
  |                        |--Find user by email----->|                   |
  |                        |  or oauth_provider_id    |                   |
  |                        |<-------Result------------|                   |
  |                        |                          |                   |
  |                        |--Create/update user----->|                   |
  |                        |<-------User--------------|                   |
  |                        |                          |                   |
  |                        |--Generate JWT token----->|                   |
  |                        |                          |                   |
  |<--200 {access_token}---|                          |                   |
  |                        |                          |                   |
```

#### Authenticated Request Flow

```
Client                    API                     Database
  |                        |                          |
  |--GET /profiles/me----->|                          |
  |  Authorization:        |                          |
  |  Bearer {token}        |                          |
  |                        |--Decode JWT token------->|
  |                        |                          |
  |                        |--Get user by ID--------->|
  |                        |<-------User--------------|
  |                        |                          |
  |                        |--Get profile with------->|
  |                        |  related entities        |
  |                        |<-------Profile-----------|
  |                        |                          |
  |<--200 {profile}--------|                          |
  |                        |                          |
```

### Onboarding Flow Design

#### Step Progression

```
Step 0: Initial state (created on user registration)
Step 1: Basic info (age, gender, height, weight)
Step 2: Fitness level (beginner, intermediate, advanced)
Step 3: Fitness goals (fat loss, muscle gain, general fitness)
Step 4: Target metrics (weight, body fat %)
Step 5: Physical constraints (equipment, injuries)
Step 6: Dietary preferences (diet type, allergies)
Step 7: Meal planning (calorie target, macros)
Step 8: Meal schedule (meal times, notifications)
Step 9: Workout schedule (days, times, notifications)
Step 10: Hydration preferences (water target, reminders)
Step 11: Lifestyle baseline (energy, stress, sleep)
Complete: Create locked profile
```

#### Step Validation Logic

Each step has specific validation rules:

**Step 1 (Basic Info)**:
- Age: 13-100
- Gender: male, female, other
- Height: 100-250 cm
- Weight: 30-300 kg

**Step 2 (Fitness Level)**:
- fitness_level: beginner, intermediate, advanced

**Step 3 (Fitness Goals)**:
- goal_type: fat_loss, muscle_gain, general_fitness
- Can have multiple goals with priorities

**Step 7 (Meal Planning)**:
- daily_calorie_target: 1000-5000
- Macros must sum to 100%
- Each macro: 0-100%

**Step 9 (Workout Schedule)**:
- day_of_week: 0-6
- At least 1 workout day required

### Profile Locking Mechanism

#### Lock States

1. **Unlocked** (is_locked = False):
   - During onboarding
   - After explicit unlock request
   - Allows modifications without version tracking

2. **Locked** (is_locked = True):
   - After onboarding completion
   - Default state for active profiles
   - Requires explicit unlock or reason for modifications

#### Version Creation Logic

```python
async def create_profile_version(profile: UserProfile, reason: str) -> UserProfileVersion:
    # Get current version number
    latest_version = await db.execute(
        select(func.max(UserProfileVersion.version_number))
        .where(UserProfileVersion.profile_id == profile.id)
    )
    next_version = (latest_version.scalar() or 0) + 1
    
    # Create snapshot of current state
    snapshot = {
        "fitness_level": profile.fitness_level,
        "fitness_goals": [serialize_goal(g) for g in profile.fitness_goals],
        "physical_constraints": [serialize_constraint(c) for c in profile.physical_constraints],
        # ... all related entities
    }
    
    # Create version record
    version = UserProfileVersion(
        profile_id=profile.id,
        version_number=next_version,
        change_reason=reason,
        snapshot=snapshot
    )
    
    return version
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I've identified the following testable properties. Some criteria have been combined to eliminate redundancy:

**Combined Properties**:
- Criteria 3.2 and 3.3 (timestamp management) can be combined into a single property about automatic timestamp handling
- Criteria 1.7 and 1.3 (JWT token structure) can be combined into a comprehensive token generation property
- Criteria 5.3, 6.3, and 6.4 (profile versioning) can be combined into a single versioning property
- Criteria 7.2, 7.3, 7.4 (fitness goals associations) are redundant with the general relationship property

**Eliminated Redundancies**:
- Individual entity association properties (7.4, 8.5, 9.5, 10.5, 11.5, 12.6) are covered by the general profile relationship property (5.5)
- OAuth user password nullability (1.13) is covered by OAuth user creation property (1.12)

### Authentication Properties

**Property 1: User Registration Creates Valid Account**

*For any* valid registration data (email, password, full_name), creating a user account should result in a user with a UUID identifier, hashed password, and initialized onboarding state at step 0.

**Validates: Requirements 1.1, 4.1**

**Property 2: Password Hashing Security**

*For any* password provided during registration, the stored password should be hashed using bcrypt and should never match the plain text password.

**Validates: Requirements 1.5**

**Property 3: JWT Token Structure and Validity**

*For any* valid user login, the generated JWT token should use HS256 algorithm, contain the user_id in the payload, have a 24-hour expiration, and be verifiable using the secret key.

**Validates: Requirements 1.3, 1.6, 1.7**

**Property 4: Token Authentication**

*For any* valid JWT token presented in the Authorization header, the system should extract the user_id, validate the signature and expiration, and grant access to the authenticated user's resources.

**Validates: Requirements 1.6**

**Property 5: OAuth User Creation**

*For any* valid Google OAuth authentication for a new user, the system should create a user account with oauth_provider='google', oauth_provider_user_id set, and hashed_password as null.

**Validates: Requirements 1.12, 1.13**

### Database Properties

**Property 6: Automatic Timestamp Management**

*For any* entity creation or update, the system should automatically set created_at on creation and updated_at on modification, both as UTC timestamps.

**Validates: Requirements 3.2, 3.3**

**Property 7: UUID Primary Keys**

*For any* created entity, the id field should be a valid UUID (version 4).

**Validates: Requirements 3.4**

**Property 8: Soft Delete Behavior**

*For any* entity deletion, the system should set the deleted_at timestamp without physically removing the record, and the entity should be excluded from subsequent queries.

**Validates: Requirements 3.6, 16.3**

### Onboarding Properties

**Property 9: Onboarding Step Validation**

*For any* onboarding step submission, if the data is invalid according to step-specific rules, the system should reject it with validation errors and not advance the step counter.

**Validates: Requirements 4.2, 4.4**

**Property 10: Onboarding Step Progression**

*For any* valid onboarding step data submission, the system should save the data and advance the current_step by 1, maintaining step_data in JSONB format.

**Validates: Requirements 4.3**

**Property 11: Onboarding State Retrieval**

*For any* user with an onboarding state, retrieving the state should return the current step number, completion status, and all step data.

**Validates: Requirements 4.7**

### Profile Management Properties

**Property 12: Single Active Profile Per User**

*For any* user, there should be at most one user_profile record where deleted_at is null.

**Validates: Requirements 5.2**

**Property 13: Profile Versioning on Modification**

*For any* profile modification (create or update), the system should create a new profile_version record with an incremented version_number, the change_reason, and a complete snapshot of the profile state.

**Validates: Requirements 5.3, 6.3, 6.4**

**Property 14: Profile Response Completeness**

*For any* profile retrieval request, the response should include all related entities: fitness_goals, physical_constraints, dietary_preferences, meal_plan, meal_schedules, workout_schedules, hydration_preferences, and lifestyle_baseline.

**Validates: Requirements 5.5**

**Property 15: Profile Lock Enforcement**

*For any* locked profile (is_locked=true), modification attempts without an explicit unlock or reason should be rejected with a 403 error.

**Validates: Requirements 6.2**

**Property 16: Profile Lock Persistence**

*For any* profile modification, the is_locked status should remain unchanged unless explicitly modified in the update request.

**Validates: Requirements 6.5**

### Data Validation Properties

**Property 17: Meal Plan Macro Validation**

*For any* meal plan creation or update, if the sum of protein_percentage, carbs_percentage, and fats_percentage does not equal 100, the system should reject the request with a validation error.

**Validates: Requirements 10.3**

**Property 18: Fitness Goal Target Ranges**

*For any* fitness goal with target values, target_weight_kg should be between 30-300 and target_body_fat_percentage should be between 1-50, otherwise the system should reject with validation errors.

**Validates: Requirements 7.5**

**Property 19: Lifestyle Rating Ranges**

*For any* lifestyle baseline, energy_level, stress_level, and sleep_quality should each be between 1-10 inclusive, otherwise the system should reject with validation errors.

**Validates: Requirements 12.3, 12.4, 12.5**

**Property 20: Workout Schedule Day Validation**

*For any* workout schedule, day_of_week should be between 0-6 inclusive (Monday-Sunday), otherwise the system should reject with validation errors.

**Validates: Requirements 11.4**

### Error Handling Properties

**Property 21: Validation Error Responses**

*For any* API request with invalid data (failing Pydantic validation), the system should return HTTP 422 with detailed field-level validation errors.

**Validates: Requirements 14.1, 14.6**

**Property 22: Resource Not Found Responses**

*For any* API request for a non-existent resource, the system should return HTTP 404 with a descriptive message.

**Validates: Requirements 14.2, 5.6**

**Property 23: Authentication Error Responses**

*For any* API request with missing, invalid, or expired authentication token, the system should return HTTP 401 with an appropriate message.

**Validates: Requirements 14.3, 1.8**

**Property 24: Authorization Error Responses**

*For any* API request attempting unauthorized actions (e.g., modifying locked profile), the system should return HTTP 403 with an appropriate message.

**Validates: Requirements 14.4**

### Data Privacy Properties

**Property 25: Soft Delete Cascade**

*For any* user deletion request, the system should set deleted_at on the user record and all related records (profile, onboarding_state, goals, preferences, schedules).

**Validates: Requirements 16.2**

**Property 26: Deleted Record Exclusion**

*For any* database query, records with non-null deleted_at should be automatically excluded from results unless explicitly requested.

**Validates: Requirements 16.3**

**Property 27: Sensitive Data Protection**

*For any* log entry or error message, passwords, JWT tokens, and OAuth tokens should never appear in plain text.

**Validates: Requirements 16.5**

## Error Handling

### Error Response Format

All API errors follow a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "field_errors": {  // Only for validation errors
    "field_name": ["Error message 1", "Error message 2"]
  }
}
```

### HTTP Status Codes

- **200 OK**: Successful GET, PATCH requests
- **201 Created**: Successful POST requests creating resources
- **400 Bad Request**: Business logic errors (e.g., onboarding incomplete, profile locked)
- **401 Unauthorized**: Missing, invalid, or expired authentication
- **403 Forbidden**