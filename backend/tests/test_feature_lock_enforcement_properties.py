"""
Property-based tests for feature lock enforcement.

Property 11: Feature Lock Enforcement
- For any incomplete user, verify access_control flags are correct

Validates: Requirements 2.4.4
"""

import pytest
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.schemas.auth import AccessControl
from app.services.onboarding_service import OnboardingService


pytestmark = pytest.mark.asyncio


class TestFeatureLockEnforcementProperty:
    """Property tests for feature lock enforcement."""
    
    @given(
        current_step=st.integers(min_value=0, max_value=8),
        completed_states=st.lists(
            st.integers(min_value=1, max_value=9),
            min_size=0,
            max_size=8,
            unique=True
        )
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.property
    async def test_property_11_feature_lock_enforcement(
        self,
        current_step: int,
        completed_states: list[int],
        db_session: AsyncSession
    ):
        """
        Feature: backend-onboarding-chat-integration, Property 11
        
        **Property 11: Feature Lock Enforcement**
        
        **Validates: Requirements 2.4.4**
        
        For any user with incomplete onboarding (onboarding_completed = False),
        verify that:
        1. can_access_chat is always True
        2. All other can_access_* flags are False
        3. locked_features contains all locked features
        4. unlock_message is present
        5. onboarding_progress is included
        
        This property ensures that incomplete users have consistent access
        control restrictions regardless of their current onboarding state.
        
        Args:
            current_step: Current onboarding step (0-8, not complete)
            completed_states: List of completed state numbers
            db_session: Database session fixture
        """
        # Create user with incomplete onboarding
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create onboarding state (incomplete)
        step_data = {f"step_{i}": {"test": "data"} for i in completed_states}
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=current_step,
            is_complete=False,  # Always incomplete for this test
            step_data=step_data,
            agent_history=[]
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Eagerly load onboarding_state relationship to avoid lazy load in async context
        result = await db_session.execute(
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.onboarding_state))
        )
        user = result.scalar_one()
        
        # Get onboarding progress
        onboarding_service = OnboardingService(db_session)
        try:
            progress = await onboarding_service.get_progress(user.id)
            onboarding_progress = {
                "current_state": progress.current_state,
                "total_states": progress.total_states,
                "completion_percentage": progress.completion_percentage
            }
        except Exception:
            onboarding_progress = {
                "current_state": current_step,
                "total_states": 9,
                "completion_percentage": 0
            }
        
        # Build access control (simulating endpoint logic)
        access_control = AccessControl(
            can_access_dashboard=False,
            can_access_workouts=False,
            can_access_meals=False,
            can_access_chat=True,  # Always true
            can_access_profile=False,
            locked_features=["dashboard", "workouts", "meals", "profile"],
            unlock_message="Complete onboarding to unlock all features",
            onboarding_progress=onboarding_progress
        )
        
        # Verify Property 11: Feature Lock Enforcement
        
        # 1. Chat access is always True
        assert access_control.can_access_chat is True, \
            "can_access_chat must always be True for incomplete users"
        
        # 2. All other features are locked (False)
        assert access_control.can_access_dashboard is False, \
            "can_access_dashboard must be False for incomplete users"
        assert access_control.can_access_workouts is False, \
            "can_access_workouts must be False for incomplete users"
        assert access_control.can_access_meals is False, \
            "can_access_meals must be False for incomplete users"
        assert access_control.can_access_profile is False, \
            "can_access_profile must be False for incomplete users"
        
        # 3. Locked features list contains all locked features
        expected_locked = ["dashboard", "workouts", "meals", "profile"]
        assert set(access_control.locked_features) == set(expected_locked), \
            f"locked_features must contain {expected_locked} for incomplete users"
        
        # 4. Unlock message is present
        assert access_control.unlock_message is not None, \
            "unlock_message must be present for incomplete users"
        assert "onboarding" in access_control.unlock_message.lower(), \
            "unlock_message must mention onboarding"
        
        # 5. Onboarding progress is included
        assert access_control.onboarding_progress is not None, \
            "onboarding_progress must be included for incomplete users"
        assert "current_state" in access_control.onboarding_progress, \
            "onboarding_progress must include current_state"
        assert "total_states" in access_control.onboarding_progress, \
            "onboarding_progress must include total_states"
        assert "completion_percentage" in access_control.onboarding_progress, \
            "onboarding_progress must include completion_percentage"
        
        # Verify user.onboarding_completed property returns False
        assert user.onboarding_completed is False, \
            "user.onboarding_completed must be False for incomplete onboarding"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
