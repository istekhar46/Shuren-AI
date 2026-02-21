# Technical Requirements Document: Tool Permission Scoping and Access Control

## Document Information

**Version:** 1.0  
**Date:** February 10, 2026  
**Status:** Draft  
**Related Documents:** 
- TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md
- backend_schema.md

---

## Executive Summary

This document specifies a comprehensive permission and access control system for AI agent tools in the Shuren fitness coaching platform. The system addresses security, authorization, and audit requirements across both LiveKit voice agents and LangChain text agents.

### Problem Statement

The current implementation lacks explicit permission scoping for agent tools, creating several risks:

1. **Unauthorized Access**: All tools are available to all users regardless of subscription tier or onboarding status
2. **No Rate Limiting**: Users can abuse expensive operations (database writes, LLM calls)
3. **Missing Audit Trail**: Tool invocations are not tracked for security or compliance
4. **Context Validation Gap**: Tools don't verify user state before execution
5. **Dual-Layer Complexity**: LiveKit function tools and LangChain tools require separate permission enforcement

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT REQUEST                            │
│              (Voice via LiveKit / Text via FastAPI)          │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│ LIVEKIT AGENT  │    │   FASTAPI ENDPOINT  │
│  @function_tool │    │   REST Handler      │
└────────┬────────┘    └──────────┬──────────┘
         │                        │
         │  Permission Check #1   │
         │  (LiveKit Layer)       │
         │                        │
         └────────┬───────────────┘
                  │
         ┌────────▼────────┐
         │  ORCHESTRATOR   │
         │  Route Query    │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │ SPECIALIZED     │
         │ AGENT           │
         │ @tool decorator │
         └────────┬────────┘
                  │
                  │  Permission Check #2
                  │  (LangChain Layer)
                  │
         ┌────────▼────────┐
         │ DATABASE/       │
         │ EXTERNAL API    │
         └─────────────────┘
```

**Key Principle:** Defense in depth - permissions enforced at multiple layers with audit logging at each checkpoint.

---

## 1. Core Requirements

### Requirement 1.1: Permission Model

**Requirement:** THE System SHALL implement a hierarchical permission model based on subscription tiers and user state.

#### Permission Structure

```python
# Permission format: "domain:action"
# Examples:
#   - "workout:read"    - View workout plans
#   - "workout:write"   - Log workouts and modify plans
#   - "meal:read"       - View meal plans
#   - "supplement:access" - Access supplement guidance
```

#### Subscription Tiers

| Tier | Permissions | Features |
|------|-------------|----------|
| **Free** | `workout:read`, `workout:write`, `meal:read`, `meal:write` | Basic workout/meal plans, logging |
| **Premium** | Free + `supplement:access`, `progress:read`, `analytics:basic` | Supplement guidance, progress tracking |
| **Pro** | Premium + `analytics:advanced`, `priority:support` | Advanced analytics, priority support |


#### User State Requirements

| State | Required for | Blocked Actions |
|-------|--------------|-----------------|
| **Onboarding Incomplete** | All new users | Cannot log workouts, access meal plans |
| **Onboarding Complete** | Basic feature access | None (tier-based only) |
| **Profile Locked** | Admin action | All write operations blocked |
| **Subscription Expired** | Payment failure | Premium/Pro features blocked |

#### Acceptance Criteria

1. THE System SHALL define permissions using the format `"domain:action"`
2. THE System SHALL map subscription tiers to permission sets
3. THE System SHALL enforce onboarding completion before allowing workout/meal logging
4. THE System SHALL support profile locking that blocks all write operations
5. THE System SHALL gracefully degrade features when subscription expires
6. THE System SHALL store user permissions in the database for efficient lookup

---

### Requirement 1.2: AgentContext Permission Fields

**Requirement:** THE System SHALL extend AgentContext to include permission and authorization data.

#### Implementation

```python
# app/agents/context.py
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentContext(BaseModel):
    """Immutable user context with permission data"""
    
    # Existing fields
    user_id: str
    fitness_level: str
    primary_goal: str
    energy_level: str
    current_workout_plan: dict
    current_meal_plan: dict
    conversation_history: list[dict] = []
    
    # NEW: Permission and authorization fields
    permissions: List[str] = Field(default_factory=list)
    subscription_tier: str = "free"  # "free" | "premium" | "pro"
    onboarding_complete: bool = False
    profile_locked: bool = False
    subscription_expires_at: Optional[datetime] = None
    
    # NEW: Rate limiting state
    rate_limit_state: dict = Field(default_factory=dict)
    
    # Helper methods
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def can_write_workouts(self) -> bool:
        """Check if user can log workouts."""
        return (
            self.onboarding_complete 
            and not self.profile_locked
            and self.has_permission("workout:write")
        )
    
    def can_access_premium_features(self) -> bool:
        """Check if user has active premium access."""
        if self.subscription_tier not in ["premium", "pro"]:
            return False
        
        # Check expiration
        if self.subscription_expires_at:
            return datetime.utcnow() < self.subscription_expires_at
        
        return True
    
    def is_subscription_active(self) -> bool:
        """Check if subscription is active."""
        if self.subscription_tier == "free":
            return True  # Free tier never expires
        
        if self.subscription_expires_at:
            return datetime.utcnow() < self.subscription_expires_at
        
        return True
```

#### Acceptance Criteria

1. THE AgentContext SHALL include `permissions: List[str]` field
2. THE AgentContext SHALL include `subscription_tier: str` field
3. THE AgentContext SHALL include `onboarding_complete: bool` field
4. THE AgentContext SHALL include `profile_locked: bool` field
5. THE AgentContext SHALL include `subscription_expires_at: Optional[datetime]` field
6. THE AgentContext SHALL provide helper methods for common permission checks
7. THE AgentContext SHALL remain immutable (Pydantic BaseModel with no setters)

---

### Requirement 1.3: Context Loader Permission Integration

**Requirement:** THE System SHALL load user permissions when building AgentContext.

#### Implementation

```python
# app/services/context_loader.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.preferences import UserProfile
from app.agents.context import AgentContext

# Permission mapping by tier
TIER_PERMISSIONS = {
    "free": [
        "workout:read",
        "workout:write",
        "meal:read",
        "meal:write",
    ],
    "premium": [
        "workout:read",
        "workout:write",
        "meal:read",
        "meal:write",
        "supplement:access",
        "progress:read",
        "analytics:basic",
    ],
    "pro": [
        "workout:read",
        "workout:write",
        "meal:read",
        "meal:write",
        "supplement:access",
        "progress:read",
        "analytics:basic",
        "analytics:advanced",
        "priority:support",
    ]
}

async def load_agent_context(
    db: AsyncSession,
    user_id: str,
    include_history: bool = False
) -> AgentContext:
    """
    Load complete agent context including permissions.
    
    Args:
        db: Async database session
        user_id: User's unique identifier
        include_history: Whether to load conversation history
    
    Returns:
        AgentContext with all user data and permissions
    
    Raises:
        ValueError: If user or profile not found
    """
    # Load user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Load profile
    stmt = select(UserProfile).where(
        UserProfile.user_id == user_id,
        UserProfile.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise ValueError(f"Profile not found for user {user_id}")
    
    # Determine permissions based on tier
    tier = profile.subscription_tier or "free"
    permissions = TIER_PERMISSIONS.get(tier, TIER_PERMISSIONS["free"])
    
    # Load conversation history if requested
    conversation_history = []
    if include_history:
        conversation_history = await _load_conversation_history(db, user_id)
    
    # Build context
    return AgentContext(
        user_id=str(user_id),
        fitness_level=profile.fitness_level,
        primary_goal=profile.primary_goal,
        energy_level=profile.energy_level or "medium",
        current_workout_plan=await _load_workout_plan(db, user_id),
        current_meal_plan=await _load_meal_plan(db, user_id),
        conversation_history=conversation_history,
        
        # Permission fields
        permissions=permissions,
        subscription_tier=tier,
        onboarding_complete=profile.onboarding_complete,
        profile_locked=profile.profile_locked or False,
        subscription_expires_at=profile.subscription_expires_at,
        rate_limit_state={}
    )
```

#### Acceptance Criteria

1. THE context loader SHALL query user subscription tier from database
2. THE context loader SHALL map subscription tier to permission list
3. THE context loader SHALL load onboarding completion status
4. THE context loader SHALL load profile lock status
5. THE context loader SHALL load subscription expiration date
6. THE context loader SHALL populate all permission fields in AgentContext
7. THE context loader SHALL use a constant mapping for tier-to-permissions

---

## 2. Permission Enforcement Layer

### Requirement 2.1: Permission Decorator

**Requirement:** THE System SHALL provide a decorator for enforcing permissions on agent tools.


#### Implementation

```python
# app/core/permissions.py
from functools import wraps
from typing import Callable, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PermissionDenied(Exception):
    """Raised when user lacks permission for a tool."""
    
    def __init__(self, message: str, required_permission: str):
        self.message = message
        self.required_permission = required_permission
        super().__init__(message)

def require_permissions(*required_perms: str):
    """
    Decorator to enforce permissions on agent tools.
    
    This decorator checks if the user has all required permissions before
    executing the tool. It also logs the permission check for audit purposes.
    
    Args:
        *required_perms: Permission strings like "workout:read", "meal:write"
    
    Raises:
        PermissionDenied: If user lacks any required permission
    
    Example:
        @require_permissions("workout:write")
        async def log_workout_set(exercise: str, reps: int) -> str:
            # Tool implementation
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context from function arguments
            # Assumes first arg is self with context attribute
            context = None
            
            if args and hasattr(args[0], 'context'):
                context = args[0].context
            elif args and hasattr(args[0], 'user_context'):
                context = args[0].user_context
            else:
                raise ValueError(
                    f"Tool {func.__name__} must have access to user context"
                )
            
            # Check each required permission
            for perm in required_perms:
                if not context.has_permission(perm):
                    logger.warning(
                        f"Permission denied: user={context.user_id} "
                        f"lacks '{perm}' for tool={func.__name__}"
                    )
                    
                    # Raise with user-friendly message
                    raise PermissionDenied(
                        message=_get_permission_denied_message(perm, context),
                        required_permission=perm
                    )
            
            # Log successful permission check
            logger.info(
                f"Permission granted: user={context.user_id} "
                f"tool={func.__name__} permissions={required_perms}"
            )
            
            # Execute tool
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def _get_permission_denied_message(permission: str, context) -> str:
    """Generate user-friendly permission denied message."""
    
    # Check if onboarding incomplete
    if not context.onboarding_complete:
        return (
            "Please complete your onboarding profile before using this feature. "
            "I can guide you through it if you'd like!"
        )
    
    # Check if profile locked
    if context.profile_locked:
        return (
            "Your profile is currently locked. "
            "Please contact support for assistance."
        )
    
    # Check if subscription expired
    if not context.is_subscription_active():
        return (
            "This feature requires an active subscription. "
            "Would you like to learn about our premium plans?"
        )
    
    # Check if premium feature
    if permission in ["supplement:access", "analytics:advanced"]:
        return (
            f"This feature is available with a premium subscription. "
            f"Your current plan is {context.subscription_tier}. "
            f"Would you like to upgrade?"
        )
    
    # Generic message
    return (
        f"You don't have permission to use this feature. "
        f"Required: {permission}"
    )
```

#### Acceptance Criteria

1. THE decorator SHALL check all required permissions before tool execution
2. THE decorator SHALL raise `PermissionDenied` exception on failure
3. THE decorator SHALL log permission checks (both success and failure)
4. THE decorator SHALL provide user-friendly error messages
5. THE decorator SHALL extract context from function arguments automatically
6. THE decorator SHALL support multiple required permissions
7. THE decorator SHALL preserve function metadata using `@wraps`

---

### Requirement 2.2: Rate Limiting

**Requirement:** THE System SHALL implement rate limiting to prevent abuse of expensive operations.

#### Implementation

```python
# app/core/rate_limiting.py
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int):
        self.message = message
        self.retry_after = retry_after  # seconds
        super().__init__(message)

class RateLimiter:
    """
    In-memory rate limiter for agent tools.
    
    Uses sliding window algorithm to track tool invocations per user.
    For production, consider Redis-based implementation for distributed systems.
    """
    
    def __init__(self):
        # Structure: {user_id: {tool_name: [(timestamp, count)]}}
        self._windows: Dict[str, Dict[str, list]] = {}
    
    async def check_rate_limit(
        self,
        user_id: str,
        tool_name: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if user has exceeded rate limit for a tool.
        
        Args:
            user_id: User's unique identifier
            tool_name: Name of the tool being invoked
            limit: Maximum invocations allowed in window
            window_seconds: Time window in seconds (default: 60)
        
        Returns:
            True if within limit, False if exceeded
        
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Initialize user tracking
        if user_id not in self._windows:
            self._windows[user_id] = {}
        
        if tool_name not in self._windows[user_id]:
            self._windows[user_id][tool_name] = []
        
        # Get invocations in current window
        invocations = self._windows[user_id][tool_name]
        
        # Remove old invocations outside window
        invocations = [
            (ts, count) for ts, count in invocations
            if ts > window_start
        ]
        
        # Count total invocations in window
        total_count = sum(count for _, count in invocations)
        
        # Check limit
        if total_count >= limit:
            retry_after = int((invocations[0][0] - window_start).total_seconds())
            
            logger.warning(
                f"Rate limit exceeded: user={user_id} tool={tool_name} "
                f"count={total_count} limit={limit}"
            )
            
            raise RateLimitExceeded(
                message=f"You're using this feature too quickly. Please wait {retry_after} seconds.",
                retry_after=retry_after
            )
        
        # Record this invocation
        invocations.append((now, 1))
        self._windows[user_id][tool_name] = invocations
        
        logger.debug(
            f"Rate limit check passed: user={user_id} tool={tool_name} "
            f"count={total_count + 1}/{limit}"
        )
        
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int, window_seconds: int = 60):
    """
    Decorator to enforce rate limiting on agent tools.
    
    Args:
        limit: Maximum invocations allowed in window
        window_seconds: Time window in seconds (default: 60)
    
    Example:
        @rate_limit(limit=30, window_seconds=60)
        async def log_workout_set(exercise: str, reps: int) -> str:
            # Tool implementation
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context
            context = None
            if args and hasattr(args[0], 'context'):
                context = args[0].context
            elif args and hasattr(args[0], 'user_context'):
                context = args[0].user_context
            
            if context:
                # Check rate limit
                await rate_limiter.check_rate_limit(
                    user_id=context.user_id,
                    tool_name=func.__name__,
                    limit=limit,
                    window_seconds=window_seconds
                )
            
            # Execute tool
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

#### Rate Limit Configuration

| Tool Category | Limit | Window | Rationale |
|---------------|-------|--------|-----------|
| Workout Logging | 30 calls | 60 seconds | Prevent spam during workouts |
| Meal Logging | 20 calls | 60 seconds | Typical meal logging frequency |
| Plan Modifications | 5 calls | 300 seconds | Expensive LLM operations |
| Database Queries | 60 calls | 60 seconds | Prevent database overload |

#### Acceptance Criteria

1. THE System SHALL implement sliding window rate limiting
2. THE System SHALL track invocations per user per tool
3. THE System SHALL raise `RateLimitExceeded` when limit exceeded
4. THE System SHALL provide retry-after time in exception
5. THE System SHALL clean up old invocation records outside window
6. THE System SHALL log rate limit violations
7. THE System SHALL support configurable limits per tool

---

### Requirement 2.3: Audit Logging

**Requirement:** THE System SHALL log all tool invocations for security and compliance auditing.


#### Implementation

```python
# app/core/audit.py
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
import logging
import json

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Audit logger for agent tool invocations.
    
    Logs all tool calls to database for security, compliance, and analytics.
    """
    
    @staticmethod
    async def log_tool_invocation(
        db: AsyncSession,
        user_id: str,
        tool_name: str,
        agent_type: str,
        arguments: Dict[str, Any],
        result: Optional[str] = None,
        error: Optional[str] = None,
        permission_check: bool = True,
        rate_limit_check: bool = True,
        execution_time_ms: Optional[int] = None
    ) -> None:
        """
        Log a tool invocation to the audit table.
        
        Args:
            db: Async database session
            user_id: User who invoked the tool
            tool_name: Name of the tool
            agent_type: Type of agent (workout, diet, etc.)
            arguments: Tool arguments (will be JSON serialized)
            result: Tool result (optional)
            error: Error message if tool failed (optional)
            permission_check: Whether permission check passed
            rate_limit_check: Whether rate limit check passed
            execution_time_ms: Tool execution time in milliseconds
        """
        try:
            # Create audit log entry
            from app.models.audit import ToolInvocationLog
            
            log_entry = ToolInvocationLog(
                user_id=user_id,
                tool_name=tool_name,
                agent_type=agent_type,
                arguments=json.dumps(arguments),
                result=result[:1000] if result else None,  # Truncate long results
                error=error[:500] if error else None,
                permission_check_passed=permission_check,
                rate_limit_check_passed=rate_limit_check,
                execution_time_ms=execution_time_ms,
                invoked_at=datetime.utcnow()
            )
            
            db.add(log_entry)
            await db.commit()
            
            logger.info(
                f"Audit log created: user={user_id} tool={tool_name} "
                f"success={error is None}"
            )
            
        except Exception as e:
            # Don't fail tool execution if audit logging fails
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            # Rollback to prevent transaction issues
            await db.rollback()

def audit_tool(func: Callable):
    """
    Decorator to automatically audit tool invocations.
    
    This decorator wraps tool functions and logs their invocation,
    arguments, results, and any errors to the audit table.
    
    Example:
        @audit_tool
        @require_permissions("workout:write")
        async def log_workout_set(exercise: str, reps: int) -> str:
            # Tool implementation
            pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract context and db session
        context = None
        db_session = None
        
        if args and hasattr(args[0], 'context'):
            context = args[0].context
        if args and hasattr(args[0], 'db_session'):
            db_session = args[0].db_session
        
        # Capture start time
        start_time = datetime.utcnow()
        
        # Track permission and rate limit checks
        permission_passed = True
        rate_limit_passed = True
        result = None
        error = None
        
        try:
            # Execute tool
            result = await func(*args, **kwargs)
            return result
            
        except PermissionDenied as e:
            permission_passed = False
            error = str(e)
            raise
            
        except RateLimitExceeded as e:
            rate_limit_passed = False
            error = str(e)
            raise
            
        except Exception as e:
            error = str(e)
            raise
            
        finally:
            # Calculate execution time
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Log to audit table
            if context and db_session:
                await AuditLogger.log_tool_invocation(
                    db=db_session,
                    user_id=context.user_id,
                    tool_name=func.__name__,
                    agent_type=getattr(args[0], 'agent_type', 'unknown'),
                    arguments=kwargs,
                    result=str(result) if result else None,
                    error=error,
                    permission_check=permission_passed,
                    rate_limit_check=rate_limit_passed,
                    execution_time_ms=execution_time
                )
    
    return wrapper
```

#### Database Schema

```sql
-- app/models/audit.py
CREATE TABLE tool_invocation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    tool_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    arguments JSONB NOT NULL,
    result TEXT,
    error TEXT,
    permission_check_passed BOOLEAN NOT NULL DEFAULT true,
    rate_limit_check_passed BOOLEAN NOT NULL DEFAULT true,
    execution_time_ms INTEGER,
    invoked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Indexes for common queries
    INDEX idx_tool_logs_user_id (user_id),
    INDEX idx_tool_logs_tool_name (tool_name),
    INDEX idx_tool_logs_invoked_at (invoked_at),
    INDEX idx_tool_logs_error (error) WHERE error IS NOT NULL
);
```

#### Acceptance Criteria

1. THE System SHALL log all tool invocations to database
2. THE System SHALL capture tool name, user, arguments, and result
3. THE System SHALL log permission check results
4. THE System SHALL log rate limit check results
5. THE System SHALL capture execution time in milliseconds
6. THE System SHALL truncate long results to prevent database bloat
7. THE System SHALL NOT fail tool execution if audit logging fails
8. THE System SHALL provide indexes for common audit queries

---

## 3. LiveKit Voice Agent Integration

### Requirement 3.1: LiveKit Function Tool Permissions

**Requirement:** THE System SHALL enforce permissions on LiveKit `@function_tool` decorated tools.

#### Implementation

```python
# app/livekit_agents/voice_agent_worker.py
from livekit.agents import function_tool
from app.core.permissions import require_permissions, PermissionDenied
from app.core.rate_limiting import rate_limit, RateLimitExceeded
from app.core.audit import audit_tool

class FitnessVoiceAgent(Agent):
    """Voice agent with permission-enforced tools"""
    
    @function_tool()
    @rate_limit(limit=30, window_seconds=60)
    async def log_workout_set(
        self,
        exercise: str,
        reps: int,
        weight: float
    ) -> str:
        """
        Log a completed workout set.
        
        Args:
            exercise: Name of the exercise
            reps: Number of repetitions
            weight: Weight used in kg
        
        Returns:
            Confirmation message
        """
        try:
            # Manual permission check (decorators don't work with @function_tool)
            if not self.user_context.can_write_workouts():
                if not self.user_context.onboarding_complete:
                    return (
                        "Please complete your onboarding profile before logging workouts. "
                        "Would you like me to guide you through it?"
                    )
                elif self.user_context.profile_locked:
                    return "Your profile is currently locked. Please contact support."
                else:
                    return "You don't have permission to log workouts."
            
            # Queue for async processing
            await self._log_queue.put({
                "exercise": exercise,
                "reps": reps,
                "weight": weight,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(
                f"Workout logged: user={self.user_context.user_id} "
                f"exercise={exercise} reps={reps} weight={weight}"
            )
            
            return f"Logged {reps} reps of {exercise} at {weight} kg. Great work!"
            
        except RateLimitExceeded as e:
            return e.message
        except Exception as e:
            logger.error(f"Error logging workout: {e}")
            return "I had trouble logging that set. Please try again."
    
    @function_tool()
    async def get_todays_workout(self) -> str:
        """Get today's workout plan (read-only, no permission check needed)."""
        
        # Read operations typically don't need permission checks
        # But we still validate onboarding completion
        if not self.user_context.onboarding_complete:
            return (
                "Please complete your onboarding profile first. "
                "I can help you set up your fitness plan!"
            )
        
        # Use cached context (no DB hit)
        workout = self.user_context.current_workout_plan.get("today")
        return json.dumps(workout)
    
    @function_tool()
    async def ask_specialist_agent(
        self,
        query: str,
        specialist: str
    ) -> str:
        """
        Delegate to specialist agent (permissions checked at LangChain layer).
        
        Args:
            query: User's question
            specialist: Agent type (workout, diet, supplement)
        """
        # Validate specialist type
        if specialist not in ["workout", "diet", "supplement"]:
            return "I can connect you with workout, diet, or supplement specialists."
        
        # Check premium features
        if specialist == "supplement" and not self.user_context.can_access_premium_features():
            return (
                "Supplement guidance is a premium feature. "
                "Would you like to learn about upgrading your plan?"
            )
        
        # Delegate to orchestrator (permissions checked there)
        try:
            response = await self.orchestrator.route_query(
                user_id=self.user_context.user_id,
                query=query,
                agent_type=AgentType(specialist),
                voice_mode=True
            )
            return response.content
            
        except PermissionDenied as e:
            return e.message
        except Exception as e:
            logger.error(f"Error delegating to specialist: {e}")
            return "I'm having trouble connecting to the specialist right now."
```

#### Acceptance Criteria

1. THE LiveKit function tools SHALL manually check permissions before execution
2. THE LiveKit function tools SHALL return user-friendly error messages on permission denial
3. THE LiveKit function tools SHALL check onboarding completion for write operations
4. THE LiveKit function tools SHALL check premium access for premium features
5. THE LiveKit function tools SHALL NOT raise exceptions (return error strings instead)
6. THE LiveKit function tools SHALL log permission checks
7. THE LiveKit function tools SHALL delegate complex permission checks to LangChain layer

---

## 4. LangChain Agent Tool Integration

### Requirement 4.1: LangChain Tool Permissions

**Requirement:** THE System SHALL enforce permissions on LangChain `@tool` decorated tools.


#### Implementation

```python
# app/agents/workout_planner.py
from langchain_core.tools import tool
from app.core.permissions import require_permissions, PermissionDenied
from app.core.rate_limiting import rate_limit
from app.core.audit import audit_tool
import json

class WorkoutPlannerAgent(BaseAgent):
    """Workout planner with permission-enforced tools"""
    
    def get_tools(self) -> List:
        """Get tools with permission enforcement."""
        
        # Capture context and db_session in closure
        context = self.context
        db_session = self.db_session
        
        @tool
        @audit_tool
        @require_permissions("workout:read")
        async def get_current_workout() -> str:
            """
            Get today's workout plan for the user.
            
            Returns:
                JSON string with workout details
            """
            try:
                if not db_session:
                    return json.dumps({
                        "success": False,
                        "error": "Database session not available"
                    })
                
                # Query workout plan
                # ... existing implementation ...
                
                return json.dumps({
                    "success": True,
                    "data": workout_data
                })
                
            except PermissionDenied as e:
                return json.dumps({
                    "success": False,
                    "error": e.message,
                    "required_permission": e.required_permission
                })
            except Exception as e:
                logger.error(f"Error in get_current_workout: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve workout plan"
                })
        
        @tool
        @audit_tool
        @require_permissions("workout:write")
        @rate_limit(limit=30, window_seconds=60)
        async def log_set_completion(
            exercise: str,
            reps: int,
            weight: float
        ) -> str:
            """
            Log a completed workout set.
            
            Args:
                exercise: Exercise name
                reps: Number of repetitions
                weight: Weight in kg
            
            Returns:
                JSON string with confirmation
            """
            try:
                # Create workout log entry
                from app.models.workout_log import WorkoutLog
                
                log_entry = WorkoutLog(
                    user_id=context.user_id,
                    exercise=exercise,
                    reps=reps,
                    weight_kg=weight,
                    logged_at=datetime.utcnow()
                )
                
                db_session.add(log_entry)
                await db_session.commit()
                
                return json.dumps({
                    "success": True,
                    "data": {
                        "message": f"Logged: {exercise} - {reps} reps @ {weight}kg",
                        "exercise": exercise,
                        "reps": reps,
                        "weight_kg": weight
                    }
                })
                
            except PermissionDenied as e:
                return json.dumps({
                    "success": False,
                    "error": e.message,
                    "required_permission": e.required_permission
                })
            except RateLimitExceeded as e:
                return json.dumps({
                    "success": False,
                    "error": e.message,
                    "retry_after": e.retry_after
                })
            except Exception as e:
                logger.error(f"Error in log_set_completion: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to log workout set"
                })
        
        @tool
        @audit_tool
        @require_permissions("workout:read")
        async def show_exercise_demo(exercise_name: str) -> str:
            """
            Get exercise demonstration GIF and instructions.
            
            Args:
                exercise_name: Name of the exercise
            
            Returns:
                JSON string with demo URL and instructions
            """
            try:
                # Query exercise library
                # ... existing implementation ...
                
                return json.dumps({
                    "success": True,
                    "data": exercise_data
                })
                
            except PermissionDenied as e:
                return json.dumps({
                    "success": False,
                    "error": e.message
                })
            except Exception as e:
                logger.error(f"Error in show_exercise_demo: {e}")
                return json.dumps({
                    "success": False,
                    "error": "Unable to retrieve exercise demo"
                })
        
        return [
            get_current_workout,
            log_set_completion,
            show_exercise_demo
        ]
```

#### Acceptance Criteria

1. THE LangChain tools SHALL use `@require_permissions` decorator
2. THE LangChain tools SHALL use `@rate_limit` decorator for write operations
3. THE LangChain tools SHALL use `@audit_tool` decorator for logging
4. THE LangChain tools SHALL catch `PermissionDenied` exceptions
5. THE LangChain tools SHALL catch `RateLimitExceeded` exceptions
6. THE LangChain tools SHALL return JSON with error details
7. THE LangChain tools SHALL access context via closure
8. THE LangChain tools SHALL NOT raise exceptions to LLM (return error JSON)

---

## 5. Database Schema Updates

### Requirement 5.1: User Profile Permission Fields

**Requirement:** THE System SHALL add permission-related fields to user profiles.

#### Migration

```sql
-- Migration: Add permission fields to user_profiles
ALTER TABLE user_profiles
ADD COLUMN subscription_tier VARCHAR(20) NOT NULL DEFAULT 'free',
ADD COLUMN subscription_expires_at TIMESTAMP,
ADD COLUMN profile_locked BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN profile_locked_reason TEXT,
ADD COLUMN profile_locked_at TIMESTAMP,
ADD COLUMN profile_locked_by UUID REFERENCES users(id);

-- Add check constraint for subscription tier
ALTER TABLE user_profiles
ADD CONSTRAINT check_subscription_tier 
CHECK (subscription_tier IN ('free', 'premium', 'pro'));

-- Add index for subscription queries
CREATE INDEX idx_user_profiles_subscription_tier 
ON user_profiles(subscription_tier);

-- Add index for expired subscriptions
CREATE INDEX idx_user_profiles_subscription_expires 
ON user_profiles(subscription_expires_at) 
WHERE subscription_expires_at IS NOT NULL;
```

#### Acceptance Criteria

1. THE user_profiles table SHALL include `subscription_tier` column
2. THE user_profiles table SHALL include `subscription_expires_at` column
3. THE user_profiles table SHALL include `profile_locked` column
4. THE user_profiles table SHALL include `profile_locked_reason` column
5. THE user_profiles table SHALL enforce valid subscription tier values
6. THE System SHALL create indexes for subscription queries

---

### Requirement 5.2: Tool Invocation Audit Table

**Requirement:** THE System SHALL create a table for auditing tool invocations.

#### Migration

```sql
-- Migration: Create tool_invocation_logs table
CREATE TABLE tool_invocation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    arguments JSONB NOT NULL,
    result TEXT,
    error TEXT,
    permission_check_passed BOOLEAN NOT NULL DEFAULT true,
    rate_limit_check_passed BOOLEAN NOT NULL DEFAULT true,
    execution_time_ms INTEGER,
    invoked_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_tool_logs_user_id ON tool_invocation_logs(user_id);
CREATE INDEX idx_tool_logs_tool_name ON tool_invocation_logs(tool_name);
CREATE INDEX idx_tool_logs_invoked_at ON tool_invocation_logs(invoked_at DESC);
CREATE INDEX idx_tool_logs_agent_type ON tool_invocation_logs(agent_type);

-- Partial index for errors
CREATE INDEX idx_tool_logs_errors 
ON tool_invocation_logs(user_id, invoked_at) 
WHERE error IS NOT NULL;

-- Partial index for permission denials
CREATE INDEX idx_tool_logs_permission_denied 
ON tool_invocation_logs(user_id, tool_name, invoked_at) 
WHERE permission_check_passed = false;

-- Partial index for rate limit violations
CREATE INDEX idx_tool_logs_rate_limited 
ON tool_invocation_logs(user_id, tool_name, invoked_at) 
WHERE rate_limit_check_passed = false;
```

#### SQLAlchemy Model

```python
# app/models/audit.py
from sqlalchemy import Column, String, Boolean, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class ToolInvocationLog(Base):
    """Audit log for agent tool invocations."""
    
    __tablename__ = "tool_invocation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    arguments = Column(JSONB, nullable=False)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    permission_check_passed = Column(Boolean, nullable=False, default=True)
    rate_limit_check_passed = Column(Boolean, nullable=False, default=True)
    execution_time_ms = Column(Integer, nullable=True)
    invoked_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tool_invocation_logs")
```

#### Acceptance Criteria

1. THE System SHALL create `tool_invocation_logs` table
2. THE table SHALL store user_id, tool_name, agent_type, arguments
3. THE table SHALL store result, error, and execution time
4. THE table SHALL store permission and rate limit check results
5. THE System SHALL create indexes for common audit queries
6. THE System SHALL create partial indexes for errors and violations
7. THE System SHALL cascade delete logs when user is deleted

---

## 6. Error Handling and User Experience

### Requirement 6.1: User-Friendly Error Messages

**Requirement:** THE System SHALL provide clear, actionable error messages for permission and rate limit violations.

#### Error Message Guidelines

| Scenario | Message Template | Action Suggestion |
|----------|------------------|-------------------|
| Onboarding Incomplete | "Please complete your onboarding profile before using this feature." | "I can guide you through it if you'd like!" |
| Profile Locked | "Your profile is currently locked." | "Please contact support for assistance." |
| Subscription Expired | "This feature requires an active subscription." | "Would you like to learn about our premium plans?" |
| Premium Feature | "This feature is available with a premium subscription. Your current plan is {tier}." | "Would you like to upgrade?" |
| Rate Limit Exceeded | "You're using this feature too quickly. Please wait {seconds} seconds." | None (automatic retry) |

#### Acceptance Criteria

1. THE System SHALL provide context-specific error messages
2. THE System SHALL suggest actionable next steps
3. THE System SHALL avoid technical jargon in user-facing messages
4. THE System SHALL include retry-after time for rate limits
5. THE System SHALL maintain friendly, supportive tone

---

## 7. Testing Requirements

### Requirement 7.1: Permission Testing

**Requirement:** THE System SHALL include comprehensive tests for permission enforcement.


#### Test Cases

```python
# tests/test_permissions.py
import pytest
from app.core.permissions import require_permissions, PermissionDenied
from app.agents.context import AgentContext

@pytest.mark.asyncio
async def test_permission_decorator_allows_authorized_user():
    """Test that decorator allows users with required permissions."""
    
    # Create context with permission
    context = AgentContext(
        user_id="user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high",
        permissions=["workout:write"],
        onboarding_complete=True
    )
    
    # Mock tool with permission requirement
    @require_permissions("workout:write")
    async def mock_tool(self):
        return "success"
    
    # Create mock object with context
    class MockAgent:
        def __init__(self):
            self.context = context
    
    agent = MockAgent()
    
    # Should succeed
    result = await mock_tool(agent)
    assert result == "success"

@pytest.mark.asyncio
async def test_permission_decorator_denies_unauthorized_user():
    """Test that decorator denies users without required permissions."""
    
    # Create context WITHOUT permission
    context = AgentContext(
        user_id="user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high",
        permissions=["workout:read"],  # Missing workout:write
        onboarding_complete=True
    )
    
    @require_permissions("workout:write")
    async def mock_tool(self):
        return "success"
    
    class MockAgent:
        def __init__(self):
            self.context = context
    
    agent = MockAgent()
    
    # Should raise PermissionDenied
    with pytest.raises(PermissionDenied) as exc_info:
        await mock_tool(agent)
    
    assert "workout:write" in str(exc_info.value)

@pytest.mark.asyncio
async def test_onboarding_incomplete_blocks_write_operations():
    """Test that incomplete onboarding blocks write operations."""
    
    context = AgentContext(
        user_id="user-123",
        fitness_level="beginner",
        primary_goal="fat_loss",
        energy_level="medium",
        permissions=["workout:write"],
        onboarding_complete=False  # Not complete
    )
    
    # Should not be able to write workouts
    assert not context.can_write_workouts()

@pytest.mark.asyncio
async def test_profile_locked_blocks_write_operations():
    """Test that locked profile blocks write operations."""
    
    context = AgentContext(
        user_id="user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high",
        permissions=["workout:write"],
        onboarding_complete=True,
        profile_locked=True  # Locked
    )
    
    # Should not be able to write workouts
    assert not context.can_write_workouts()

@pytest.mark.asyncio
async def test_subscription_tier_determines_permissions():
    """Test that subscription tier correctly maps to permissions."""
    
    from app.services.context_loader import TIER_PERMISSIONS
    
    # Free tier
    free_perms = TIER_PERMISSIONS["free"]
    assert "workout:read" in free_perms
    assert "workout:write" in free_perms
    assert "supplement:access" not in free_perms
    
    # Premium tier
    premium_perms = TIER_PERMISSIONS["premium"]
    assert "supplement:access" in premium_perms
    assert "analytics:basic" in premium_perms
    assert "analytics:advanced" not in premium_perms
    
    # Pro tier
    pro_perms = TIER_PERMISSIONS["pro"]
    assert "analytics:advanced" in pro_perms
```

#### Acceptance Criteria

1. THE System SHALL test permission decorator with authorized users
2. THE System SHALL test permission decorator with unauthorized users
3. THE System SHALL test onboarding completion requirements
4. THE System SHALL test profile lock enforcement
5. THE System SHALL test subscription tier permission mapping
6. THE System SHALL test multiple permission requirements
7. THE System SHALL test permission error messages

---

### Requirement 7.2: Rate Limiting Testing

**Requirement:** THE System SHALL include tests for rate limiting functionality.

#### Test Cases

```python
# tests/test_rate_limiting.py
import pytest
from app.core.rate_limiting import RateLimiter, RateLimitExceeded

@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """Test that rate limiter allows calls within limit."""
    
    limiter = RateLimiter()
    user_id = "user-123"
    tool_name = "log_workout_set"
    
    # Should allow 5 calls within limit of 10
    for i in range(5):
        result = await limiter.check_rate_limit(
            user_id=user_id,
            tool_name=tool_name,
            limit=10,
            window_seconds=60
        )
        assert result is True

@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    """Test that rate limiter blocks calls over limit."""
    
    limiter = RateLimiter()
    user_id = "user-123"
    tool_name = "log_workout_set"
    limit = 5
    
    # Make limit number of calls
    for i in range(limit):
        await limiter.check_rate_limit(
            user_id=user_id,
            tool_name=tool_name,
            limit=limit,
            window_seconds=60
        )
    
    # Next call should raise RateLimitExceeded
    with pytest.raises(RateLimitExceeded) as exc_info:
        await limiter.check_rate_limit(
            user_id=user_id,
            tool_name=tool_name,
            limit=limit,
            window_seconds=60
        )
    
    assert exc_info.value.retry_after > 0

@pytest.mark.asyncio
async def test_rate_limiter_resets_after_window():
    """Test that rate limiter resets after time window."""
    
    import asyncio
    
    limiter = RateLimiter()
    user_id = "user-123"
    tool_name = "log_workout_set"
    limit = 3
    window = 2  # 2 second window
    
    # Make limit number of calls
    for i in range(limit):
        await limiter.check_rate_limit(
            user_id=user_id,
            tool_name=tool_name,
            limit=limit,
            window_seconds=window
        )
    
    # Should be blocked
    with pytest.raises(RateLimitExceeded):
        await limiter.check_rate_limit(
            user_id=user_id,
            tool_name=tool_name,
            limit=limit,
            window_seconds=window
        )
    
    # Wait for window to expire
    await asyncio.sleep(window + 0.5)
    
    # Should be allowed again
    result = await limiter.check_rate_limit(
        user_id=user_id,
        tool_name=tool_name,
        limit=limit,
        window_seconds=window
    )
    assert result is True

@pytest.mark.asyncio
async def test_rate_limiter_per_user_isolation():
    """Test that rate limits are isolated per user."""
    
    limiter = RateLimiter()
    tool_name = "log_workout_set"
    limit = 3
    
    # User 1 makes limit calls
    for i in range(limit):
        await limiter.check_rate_limit(
            user_id="user-1",
            tool_name=tool_name,
            limit=limit,
            window_seconds=60
        )
    
    # User 1 should be blocked
    with pytest.raises(RateLimitExceeded):
        await limiter.check_rate_limit(
            user_id="user-1",
            tool_name=tool_name,
            limit=limit,
            window_seconds=60
        )
    
    # User 2 should still be allowed
    result = await limiter.check_rate_limit(
        user_id="user-2",
        tool_name=tool_name,
        limit=limit,
        window_seconds=60
    )
    assert result is True
```

#### Acceptance Criteria

1. THE System SHALL test rate limiter allows calls within limit
2. THE System SHALL test rate limiter blocks calls over limit
3. THE System SHALL test rate limiter resets after time window
4. THE System SHALL test rate limits are isolated per user
5. THE System SHALL test rate limits are isolated per tool
6. THE System SHALL test retry-after time calculation

---

## 8. Performance Considerations

### Requirement 8.1: Permission Check Performance

**Requirement:** THE System SHALL optimize permission checks to minimize latency impact.

#### Performance Targets

| Operation | Target Latency | Strategy |
|-----------|----------------|----------|
| Permission Check | < 1ms | In-memory context check |
| Rate Limit Check | < 5ms | In-memory sliding window |
| Audit Log Write | < 50ms | Async background write |
| Context Load | < 100ms | Database query with caching |

#### Optimization Strategies

1. **In-Memory Permission Checks**: Permissions loaded once into AgentContext
2. **Cached Context**: Voice mode caches context for session duration
3. **Async Audit Logging**: Audit writes don't block tool execution
4. **Indexed Queries**: Database indexes on subscription and permission fields
5. **Redis Rate Limiting**: For production, use Redis for distributed rate limiting

#### Acceptance Criteria

1. THE permission check SHALL complete in < 1ms (in-memory)
2. THE rate limit check SHALL complete in < 5ms (in-memory)
3. THE audit log write SHALL NOT block tool execution
4. THE context load SHALL complete in < 100ms with database query
5. THE System SHALL support Redis-based rate limiting for production

---

## 9. Security Considerations

### Requirement 9.1: Security Best Practices

**Requirement:** THE System SHALL follow security best practices for access control.

#### Security Principles

1. **Default Deny**: Users have no permissions by default
2. **Least Privilege**: Grant minimum permissions needed
3. **Defense in Depth**: Multiple layers of permission checks
4. **Audit Everything**: Log all tool invocations
5. **Fail Secure**: Permission check failures block execution
6. **No Privilege Escalation**: Users cannot grant themselves permissions

#### Implementation Checklist

- [ ] Permissions stored in database, not client-controlled
- [ ] Permission checks before all write operations
- [ ] Rate limiting on expensive operations
- [ ] Audit logging for compliance
- [ ] Profile locking mechanism for admin intervention
- [ ] Subscription expiration enforcement
- [ ] No hardcoded admin credentials
- [ ] Secure error messages (no sensitive data leakage)

#### Acceptance Criteria

1. THE System SHALL deny access by default
2. THE System SHALL prevent users from modifying their own permissions
3. THE System SHALL log all permission denials
4. THE System SHALL not expose sensitive data in error messages
5. THE System SHALL enforce permissions at multiple layers
6. THE System SHALL support admin profile locking

---

## 10. Deployment and Rollout

### Requirement 10.1: Phased Rollout

**Requirement:** THE System SHALL support phased rollout of permission system.

#### Rollout Phases

**Phase 1: Database Schema (Week 1)**
- Add permission fields to user_profiles
- Create tool_invocation_logs table
- Run migrations on staging environment
- Backfill existing users with "free" tier

**Phase 2: Core Permission System (Week 2)**
- Implement AgentContext permission fields
- Implement permission decorator
- Implement rate limiter
- Implement audit logger
- Unit tests for all components

**Phase 3: LangChain Integration (Week 3)**
- Apply permissions to LangChain tools
- Test with specialized agents
- Integration tests

**Phase 4: LiveKit Integration (Week 4)**
- Apply permissions to LiveKit function tools
- Test voice agent flows
- End-to-end tests

**Phase 5: Production Rollout (Week 5)**
- Deploy to staging
- Monitor audit logs
- Gradual rollout to production (10% → 50% → 100%)
- Monitor error rates and latency

#### Acceptance Criteria

1. THE System SHALL deploy database changes before code changes
2. THE System SHALL backfill existing users with default permissions
3. THE System SHALL monitor audit logs during rollout
4. THE System SHALL support rollback if issues detected
5. THE System SHALL gradually increase production traffic

---

## 11. Monitoring and Observability

### Requirement 11.1: Permission Metrics

**Requirement:** THE System SHALL expose metrics for permission system monitoring.

#### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `permission_denials_total` | Total permission denials | > 100/min |
| `rate_limit_violations_total` | Total rate limit violations | > 50/min |
| `tool_invocation_latency_ms` | Tool execution time | p95 > 500ms |
| `audit_log_write_failures` | Failed audit writes | > 10/min |
| `permission_check_latency_ms` | Permission check time | p95 > 5ms |

#### Logging

```python
# Structured logging for permission events
logger.info(
    "permission_check",
    extra={
        "user_id": user_id,
        "tool_name": tool_name,
        "required_permissions": required_perms,
        "result": "granted" | "denied",
        "reason": "onboarding_incomplete" | "profile_locked" | etc,
        "latency_ms": execution_time
    }
)
```

#### Acceptance Criteria

1. THE System SHALL expose Prometheus metrics for permission checks
2. THE System SHALL log all permission denials with structured data
3. THE System SHALL alert on high permission denial rates
4. THE System SHALL alert on high rate limit violation rates
5. THE System SHALL track permission check latency

---

## 12. Documentation Requirements

### Requirement 12.1: Developer Documentation

**Requirement:** THE System SHALL provide comprehensive documentation for permission system.

#### Documentation Deliverables

1. **Permission Model Guide**: Explanation of permission structure and tiers
2. **Tool Development Guide**: How to add permissions to new tools
3. **Testing Guide**: How to test permission-enforced tools
4. **Troubleshooting Guide**: Common permission issues and solutions
5. **API Reference**: Permission decorator and helper function documentation

#### Acceptance Criteria

1. THE System SHALL document all permission strings and their meanings
2. THE System SHALL provide examples of permission-enforced tools
3. THE System SHALL document subscription tier permission mappings
4. THE System SHALL provide troubleshooting guide for common issues
5. THE System SHALL maintain up-to-date API reference

---

## Appendix A: Permission Reference

### Complete Permission List

| Permission | Description | Tier | Category |
|------------|-------------|------|----------|
| `workout:read` | View workout plans | Free+ | Read |
| `workout:write` | Log workouts, modify plans | Free+ | Write |
| `meal:read` | View meal plans | Free+ | Read |
| `meal:write` | Log meals, modify plans | Free+ | Write |
| `supplement:access` | Access supplement guidance | Premium+ | Feature |
| `progress:read` | View progress tracking | Premium+ | Read |
| `analytics:basic` | Basic analytics dashboard | Premium+ | Feature |
| `analytics:advanced` | Advanced analytics | Pro | Feature |
| `priority:support` | Priority customer support | Pro | Feature |

---

## Appendix B: Example Tool Implementation

### Complete Example: Permission-Enforced Tool

```python
from langchain_core.tools import tool
from app.core.permissions import require_permissions
from app.core.rate_limiting import rate_limit
from app.core.audit import audit_tool

@tool
@audit_tool
@require_permissions("workout:write")
@rate_limit(limit=30, window_seconds=60)
async def log_workout_set(exercise: str, reps: int, weight: float) -> str:
    """
    Log a completed workout set.
    
    This tool records workout progress for the user. It requires:
    - Permission: workout:write
    - Rate limit: 30 calls per 60 seconds
    - Onboarding: Must be complete
    - Profile: Must not be locked
    
    Args:
        exercise: Name of the exercise (e.g., "Bench Press")
        reps: Number of repetitions completed
        weight: Weight used in kilograms
    
    Returns:
        JSON string with confirmation or error
    """
    try:
        # Tool implementation
        # ... database operations ...
        
        return json.dumps({
            "success": True,
            "data": {
                "message": f"Logged {reps} reps of {exercise} at {weight}kg",
                "exercise": exercise,
                "reps": reps,
                "weight_kg": weight
            }
        })
        
    except Exception as e:
        logger.error(f"Error logging workout: {e}")
        return json.dumps({
            "success": False,
            "error": "Unable to log workout set"
        })
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-10 | System | Initial draft |

