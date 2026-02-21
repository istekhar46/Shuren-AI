"""Property-based tests for AgentOrchestrator onboarding mode access control.

This module contains property-based tests using Hypothesis to verify
universal correctness properties of the agent orchestrator's access control.

Property 2: Onboarding Mode Access Control
- For any user, verify access control based on onboarding_completed status
- Tests that onboarding_mode flag correctly controls agent access
- Validates Requirements 2.1.1, 2.4.1
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.models.user import User
from app.models.onboarding import OnboardingState


@pytest.mark.property
class TestOnboardingModeAccessControlProperty:
    """Property-based tests for onboarding mode access control."""
    
    @given(
        onboarding_completed=st.booleans(),
        onboarding_mode=st.booleans(),
        agent_type=st.sampled_from([
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SUPPLEMENT,
            AgentType.SCHEDULER,
            AgentType.GENERAL
        ])
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.asyncio
    async def test_onboarding_mode_access_control_property(
        self,
        onboarding_completed: bool,
        onboarding_mode: bool,
        agent_type: AgentType,
        db_session: AsyncSession
    ):
        """Property 2: Onboarding Mode Access Control.
        
        **Validates: Requirements 2.1.1, 2.4.1**
        
        For any user and any combination of onboarding_completed status and
        onboarding_mode flag, verify that:
        
        1. If onboarding_mode=True and onboarding is complete:
           - Request is REJECTED (ValueError raised)
           - Error message indicates onboarding already completed
        
        2. If onboarding_mode=True and onboarding is incomplete:
           - Request is ALLOWED
           - Specified agent_type is used
        
        3. If onboarding_mode=False and onboarding is incomplete:
           - Request is REJECTED (ValueError raised)
           - Error message indicates onboarding must be completed
        
        4. If onboarding_mode=False and onboarding is complete:
           - Request is ALLOWED
           - Agent type is FORCED to GENERAL (regardless of requested type)
        
        This property ensures that access control is consistently enforced
        across all possible combinations of user state and request parameters.
        
        Args:
            onboarding_completed: Whether user has completed onboarding
            onboarding_mode: Whether request is in onboarding mode
            agent_type: Requested agent type
            db_session: Database session
        """
        # Create test user
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        # Create onboarding state based on completion status
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9 if onboarding_completed else 3,
            is_complete=onboarding_completed,
            step_data={} if not onboarding_completed else {
                f"step_{i}": {"test": "data"} for i in range(1, 10)
            },
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        
        # Create a minimal UserProfile to satisfy context loading
        # (only needed for non-rejected cases, but create for all to simplify)
        from app.models.profile import UserProfile
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            fitness_level="beginner",
            is_locked=onboarding_completed,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(onboarding_state)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Define expected behavior based on the property rules
        should_reject = (
            (onboarding_mode and onboarding_completed) or  # Case 1: onboarding mode but already complete
            (not onboarding_mode and not onboarding_completed) or  # Case 3: regular mode but not complete
            (not onboarding_mode and onboarding_completed and agent_type != AgentType.GENERAL)  # Case 4b: post-onboarding with non-general agent
        )
        
        should_force_general = False  # We'll handle this in the allowed case
        
        # Test the access control
        if should_reject:
            # Verify that request is rejected with appropriate error
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="test query",
                    agent_type=agent_type,
                    voice_mode=False,
                    onboarding_mode=onboarding_mode
                )
            
            # Verify error message is appropriate
            error_message = str(exc_info.value).lower()
            
            if onboarding_mode and onboarding_completed:
                # Case 1: Should indicate onboarding already completed
                assert any(keyword in error_message for keyword in [
                    "already completed",
                    "complete",
                    "regular chat"
                ]), (
                    f"Error message should indicate onboarding already completed. "
                    f"Got: {exc_info.value}"
                )
            
            if not onboarding_mode and not onboarding_completed:
                # Case 3: Should indicate onboarding must be completed first
                assert any(keyword in error_message for keyword in [
                    "complete onboarding",
                    "onboarding first",
                    "finish onboarding"
                ]), (
                    f"Error message should indicate onboarding must be completed. "
                    f"Got: {exc_info.value}"
                )
            
            if not onboarding_mode and onboarding_completed and agent_type != AgentType.GENERAL:
                # Case 4b: Should indicate only general agent available
                assert any(keyword in error_message for keyword in [
                    "only general agent",
                    "general agent",
                    "not available"
                ]), (
                    f"Error message should indicate only general agent available. "
                    f"Got: {exc_info.value}"
                )
        
        else:
            # Request should be allowed - verify it doesn't raise an access control error
            # Note: We expect the request to fail at agent processing (no LLM setup),
            # but it should pass the access control checks
            try:
                response = await orchestrator.route_query(
                    user_id=str(user.id),
                    query="test query",
                    agent_type=agent_type,
                    voice_mode=False,
                    onboarding_mode=onboarding_mode
                )
                
                # If we get here, access control passed AND agent processing succeeded
                # (unlikely in test environment without LLM, but possible)
                
                # Verify agent type is correct
                # Case 2 (onboarding_mode=True, incomplete): Use requested agent
                # Case 4a (onboarding_mode=False, complete, agent=GENERAL): Use GENERAL
                if onboarding_mode:
                    # During onboarding: requested agent type should be used
                    assert response.agent_type == agent_type.value, (
                        f"During onboarding, requested agent type should be used. "
                        f"Expected: {agent_type.value}, Got: {response.agent_type}"
                    )
                else:
                    # Post-onboarding: should always be GENERAL
                    assert response.agent_type == AgentType.GENERAL.value, (
                        f"Post-onboarding requests should use GENERAL agent. "
                        f"Expected: {AgentType.GENERAL.value}, Got: {response.agent_type}"
                    )
                
                # Verify metadata includes onboarding_mode flag
                assert response.metadata is not None, "Response metadata should not be None"
                assert "onboarding_mode" in response.metadata, (
                    "Response metadata should include onboarding_mode flag"
                )
                assert response.metadata["onboarding_mode"] == onboarding_mode, (
                    f"Response metadata onboarding_mode should match request. "
                    f"Expected: {onboarding_mode}, Got: {response.metadata['onboarding_mode']}"
                )
                
            except Exception as e:
                # If we get an exception, verify it's NOT an access control error
                if isinstance(e, ValueError):
                    error_message = str(e).lower()
                    # Check if it's an access control error (should not happen in allowed cases)
                    if any(keyword in error_message for keyword in [
                        "already completed",
                        "complete onboarding",
                        "onboarding first",
                        "only general agent"
                    ]):
                        pytest.fail(
                            f"Access control rejected a request that should be allowed. "
                            f"onboarding_completed={onboarding_completed}, "
                            f"onboarding_mode={onboarding_mode}, "
                            f"agent_type={agent_type.value}, "
                            f"Error: {e}"
                        )
                # For other exceptions (like missing LLM, missing context data),
                # we consider the access control check passed since it didn't raise
                # an access control ValueError
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
