"""
Integration tests for AgentOrchestrator refinement.

This module tests end-to-end flows with real database interactions,
verifying that access control, classification, and agent routing work
correctly across the entire system.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile


@pytest.mark.integration
class TestOnboardingFlowIntegration:
    """Integration tests for complete onboarding flow with agent routing."""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow_with_routing(self, db_session: AsyncSession):
        """
        Test complete onboarding flow with agent routing.
        
        Verifies:
        - Specialized agents are accessible during onboarding
        - General agent is blocked during onboarding
        - State transitions work correctly
        - Requirements: 2.1, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding (step 3 - workout phase)
        user = User(
            id=uuid4(),
            email="onboarding_test@example.com",
            hashed_password="hashed",
            full_name="Onboarding Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=3,
            is_complete=False,
            step_data={
                "step_1": {"age": 28, "gender": "male", "height_cm": 175, "weight_kg": 75},
                "step_2": {"fitness_level": "intermediate"}
            },
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(onboarding_state)
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "intermediate"
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Here's your workout plan",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Test 1: Specialized agent (WORKOUT) should be accessible
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="What exercises should I do?",
                agent_type=AgentType.WORKOUT,
                voice_mode=False,
                onboarding_mode=True
            )
            
            assert response is not None
            assert response.content == "Here's your workout plan"
            mock_get_agent.assert_called()
            
            # Verify WORKOUT agent was created
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.WORKOUT
            
            # Test 2: General agent should be BLOCKED during onboarding
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="How are you?",
                    agent_type=AgentType.GENERAL,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "general agent" in error_message
            assert "not available" in error_message
            assert "onboarding" in error_message
            
            # Test 3: Tracker agent should be BLOCKED during onboarding
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Show my progress",
                    agent_type=AgentType.TRACKER,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "tracker agent" in error_message
            assert "not available" in error_message
    
    @pytest.mark.asyncio
    async def test_onboarding_state_transitions(self, db_session: AsyncSession):
        """
        Test state transitions during onboarding.
        
        Verifies:
        - Different specialized agents accessible at different steps
        - Access control enforced at each step
        - Requirements: 2.1, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user
        user = User(
            id=uuid4(),
            email="transition_test@example.com",
            hashed_password="hashed",
            full_name="Transition Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        # Test different onboarding steps
        test_steps = [
            (1, AgentType.WORKOUT, "Step 1-3: Workout agent"),
            (4, AgentType.DIET, "Step 4-5: Diet agent"),
            (6, AgentType.SCHEDULER, "Step 6-8: Scheduler agent"),
            (9, AgentType.SUPPLEMENT, "Step 9: Supplement agent"),
        ]
        
        for step, expected_agent, description in test_steps:
            # Update onboarding state
            onboarding_state = OnboardingState(
                id=uuid4(),
                user_id=user.id,
                current_step=step,
                is_complete=False,
                step_data={f"step_{i}": {} for i in range(1, step + 1)},
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(onboarding_state)
            await db_session.commit()
            await db_session.refresh(onboarding_state)
            
            # Mock dependencies
            with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
                 patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
                
                mock_context = MagicMock()
                mock_context.fitness_level = "beginner"
                mock_load_context.return_value = mock_context
                
                mock_agent = AsyncMock()
                mock_agent.process_text = AsyncMock(return_value=MagicMock(
                    content=f"Response from {expected_agent.value}",
                    agent_type=expected_agent.value,
                    tools_used=[],
                    metadata={}
                ))
                mock_get_agent.return_value = mock_agent
                
                # Verify specialized agent is accessible
                response = await orchestrator.route_query(
                    user_id=str(user.id),
                    query=f"Query for {description}",
                    agent_type=expected_agent,
                    voice_mode=False,
                    onboarding_mode=True
                )
                
                assert response is not None, f"Failed at {description}"
                assert expected_agent.value in response.content.lower(), f"Failed at {description}"
            
            # Clean up for next iteration
            await db_session.delete(onboarding_state)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_classification_during_onboarding(self, db_session: AsyncSession):
        """
        Test query classification during onboarding.
        
        Verifies:
        - Classification returns specialized agents only
        - Onboarding-specific prompts are used
        - Requirements: 2.1, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="classification_test@example.com",
            hashed_password="hashed",
            full_name="Classification Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=3,
            is_complete=False,
            step_data={},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_init_classifier_llm') as mock_init_llm, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            # Mock classifier to return workout
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "workout"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_init_llm.return_value = mock_llm
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Workout response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query without explicit agent_type (triggers classification)
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="What exercises should I do?",
                agent_type=None,  # Will trigger classification
                voice_mode=False,
                onboarding_mode=True
            )
            
            assert response is not None
            
            # Verify classifier was called with onboarding-specific prompt
            mock_llm.ainvoke.assert_called_once()
            call_args = mock_llm.ainvoke.call_args[0][0]
            system_message = call_args[0].content.lower()
            
            # Should use onboarding classification prompt
            assert "onboarding" in system_message
            # Should NOT include post-onboarding categories
            assert "tracker" not in system_message
            assert "general" not in system_message


@pytest.mark.integration
class TestPostOnboardingFlowIntegration:
    """Integration tests for post-onboarding flow with general agent."""
    
    @pytest.mark.asyncio
    async def test_post_onboarding_flow_with_general_agent(self, db_session: AsyncSession):
        """
        Test post-onboarding flow with general agent.
        
        Verifies:
        - General agent is accessible post-onboarding
        - Specialized agents are blocked
        - General agent has full context
        - Requirements: 2.2, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="post_onboarding_test@example.com",
            hashed_password="hashed",
            full_name="Post Onboarding Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {"test": "data"} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        
        # Create user profile (post-onboarding)
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(onboarding_state)
        await db_session.refresh(profile)
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            # Mock full context (post-onboarding)
            mock_context = MagicMock()
            mock_context.fitness_level = "intermediate"
            mock_context.user_profile = profile
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="General agent response with full context",
                agent_type="general",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Test 1: General agent should be accessible
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="How are you?",
                agent_type=AgentType.GENERAL,
                voice_mode=False,
                onboarding_mode=False
            )
            
            assert response is not None
            assert "general agent" in response.content.lower()
            
            # Verify context loader was called with onboarding_mode=False
            mock_load_context.assert_called()
            call_kwargs = mock_load_context.call_args[1]
            assert call_kwargs.get('onboarding_mode') == False
            
            # Verify GENERAL agent was created
            mock_get_agent.assert_called()
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.GENERAL
            
            # Test 2: Specialized agents should be BLOCKED
            specialized_agents = [
                AgentType.WORKOUT,
                AgentType.DIET,
                AgentType.SCHEDULER,
                AgentType.SUPPLEMENT
            ]
            
            for agent_type in specialized_agents:
                with pytest.raises(ValueError) as exc_info:
                    await orchestrator.route_query(
                        user_id=str(user.id),
                        query=f"Query for {agent_type.value}",
                        agent_type=agent_type,
                        voice_mode=False,
                        onboarding_mode=False
                    )
                
                error_message = str(exc_info.value).lower()
                assert "specialized agent" in error_message
                assert "not available" in error_message
                assert "after onboarding" in error_message
    
    @pytest.mark.asyncio
    async def test_classification_forced_to_general_post_onboarding(self, db_session: AsyncSession):
        """
        Test that classification is forced to GENERAL post-onboarding.
        
        Verifies:
        - Classification can return any type
        - Result is forced to GENERAL (except TEST)
        - Override is logged
        - Requirements: 2.2, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="force_general_test@example.com",
            hashed_password="hashed",
            full_name="Force General Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_init_classifier_llm') as mock_init_llm, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "intermediate"
            mock_load_context.return_value = mock_context
            
            # Mock classifier to return WORKOUT (should be overridden to GENERAL)
            mock_llm = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "workout"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_init_llm.return_value = mock_llm
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="General agent response",
                agent_type="general",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query without explicit agent_type
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="What workout should I do?",
                agent_type=None,  # Will classify as WORKOUT but force to GENERAL
                voice_mode=False,
                onboarding_mode=False
            )
            
            assert response is not None
            
            # Verify GENERAL agent was created (not WORKOUT)
            mock_get_agent.assert_called()
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.GENERAL
    
    @pytest.mark.asyncio
    async def test_tracker_agent_forced_to_general_post_onboarding(self, db_session: AsyncSession):
        """
        Test that TRACKER agent is forced to GENERAL post-onboarding.
        
        Verifies:
        - Tracker agent type is forced to GENERAL (current implementation)
        - This aligns with the design where general agent handles all post-onboarding queries
        - Requirements: 2.2, 5.2
        
        Note: TRACKER functionality is accessed via GENERAL agent delegation,
        not as a standalone agent post-onboarding.
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="tracker_test@example.com",
            hashed_password="hashed",
            full_name="Tracker Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "intermediate"
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="General agent handling tracker query",
                agent_type="general",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # TRACKER agent type is provided but should be forced to GENERAL
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="Show my progress",
                agent_type=AgentType.TRACKER,
                voice_mode=False,
                onboarding_mode=False
            )
            
            assert response is not None
            
            # Verify GENERAL agent was created (TRACKER forced to GENERAL)
            mock_get_agent.assert_called()
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.GENERAL



@pytest.mark.integration
class TestAccessViolationsIntegration:
    """Integration tests for access control violation scenarios."""
    
    @pytest.mark.asyncio
    async def test_all_access_violation_scenarios(self, db_session: AsyncSession):
        """
        Test all access control violation scenarios.
        
        Verifies:
        - All violation scenarios raise ValueError
        - Error messages are correct and helpful
        - Logging is correct
        - Requirements: 2.3, 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Scenario 1: Onboarding already completed, trying to use onboarding mode
        user1 = User(
            id=uuid4(),
            email="violation1@example.com",
            hashed_password="hashed",
            full_name="Violation Test 1",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user1)
        
        onboarding_state1 = OnboardingState(
            id=uuid4(),
            user_id=user1.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state1)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user1.id),
                    query="Test query",
                    agent_type=AgentType.WORKOUT,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "already completed" in error_message
            assert "regular chat" in error_message
            assert str(user1.id) in str(exc_info.value)
        
        # Scenario 2: Onboarding not completed, trying to use normal mode
        user2 = User(
            id=uuid4(),
            email="violation2@example.com",
            hashed_password="hashed",
            full_name="Violation Test 2",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user2)
        
        onboarding_state2 = OnboardingState(
            id=uuid4(),
            user_id=user2.id,
            current_step=5,
            is_complete=False,
            step_data={},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state2)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user2.id),
                    query="Test query",
                    agent_type=AgentType.GENERAL,
                    voice_mode=False,
                    onboarding_mode=False
                )
            
            error_message = str(exc_info.value).lower()
            assert "complete onboarding" in error_message
            assert "5/9" in str(exc_info.value)
            assert str(user2.id) in str(exc_info.value)
        
        # Scenario 3: General agent during onboarding
        user3 = User(
            id=uuid4(),
            email="violation3@example.com",
            hashed_password="hashed",
            full_name="Violation Test 3",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user3)
        
        onboarding_state3 = OnboardingState(
            id=uuid4(),
            user_id=user3.id,
            current_step=3,
            is_complete=False,
            step_data={},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state3)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user3.id),
                    query="Test query",
                    agent_type=AgentType.GENERAL,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "general agent" in error_message
            assert "not available" in error_message
            assert "onboarding" in error_message
            assert "3/9" in str(exc_info.value)
        
        # Scenario 4: Specialized agent post-onboarding
        user4 = User(
            id=uuid4(),
            email="violation4@example.com",
            hashed_password="hashed",
            full_name="Violation Test 4",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user4)
        
        onboarding_state4 = OnboardingState(
            id=uuid4(),
            user_id=user4.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state4)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user4.id),
                    query="Test query",
                    agent_type=AgentType.WORKOUT,
                    voice_mode=False,
                    onboarding_mode=False
                )
            
            error_message = str(exc_info.value).lower()
            assert "specialized agent" in error_message
            assert "workout" in error_message
            assert "not available" in error_message
            assert "after onboarding" in error_message
        
        # Scenario 5: Tracker agent during onboarding
        user5 = User(
            id=uuid4(),
            email="violation5@example.com",
            hashed_password="hashed",
            full_name="Violation Test 5",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user5)
        
        onboarding_state5 = OnboardingState(
            id=uuid4(),
            user_id=user5.id,
            current_step=3,
            is_complete=False,
            step_data={},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state5)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user5.id),
                    query="Test query",
                    agent_type=AgentType.TRACKER,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "tracker agent" in error_message
            assert "not available" in error_message
            assert "onboarding" in error_message
    
    @pytest.mark.asyncio
    async def test_access_violation_logging(self, db_session: AsyncSession, caplog):
        """
        Test that access violations are logged correctly.
        
        Verifies:
        - Violations are logged as warnings
        - Log messages include context
        - Requirements: 2.3, 5.2
        """
        import logging
        
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="logging_test@example.com",
            hashed_password="hashed",
            full_name="Logging Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            # Trigger access violation
            with caplog.at_level(logging.WARNING):
                with pytest.raises(ValueError):
                    await orchestrator.route_query(
                        user_id=str(user.id),
                        query="Test query",
                        agent_type=AgentType.WORKOUT,
                        voice_mode=False,
                        onboarding_mode=True  # Violation: onboarding already completed
                    )
            
            # Verify warning was logged
            warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
            assert len(warning_records) >= 1
            
            log_message = warning_records[0].message.lower()
            assert "access control violation" in log_message
            assert str(user.id) in warning_records[0].message
            assert "reason" in log_message


@pytest.mark.integration
class TestRealDatabaseIntegration:
    """Integration tests with real database operations."""
    
    @pytest.mark.asyncio
    async def test_with_real_user_and_onboarding_state(self, db_session: AsyncSession):
        """
        Test with real user and onboarding state from database.
        
        Verifies:
        - Context loading works with real data
        - Agent creation works with real context
        - Database queries execute correctly
        - Requirements: 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create real user with all required data
        user = User(
            id=uuid4(),
            email="real_db_test@example.com",
            hashed_password="hashed_password_123",
            full_name="Real DB Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        # Create real onboarding state with complete data
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=3,
            is_complete=False,
            step_data={
                "step_1": {
                    "age": 28,
                    "gender": "male",
                    "height_cm": 175,
                    "weight_kg": 75
                },
                "step_2": {
                    "fitness_level": "intermediate"
                },
                "step_3": {
                    "goals": [
                        {
                            "goal_type": "muscle_gain",
                            "target_weight_kg": 80,
                            "priority": 1
                        }
                    ]
                }
            },
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        
        # Create user profile (required for context loading)
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=False,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(onboarding_state)
        await db_session.refresh(profile)
        
        # Mock only the agent and LLM, use real context loading
        with patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Real database test response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query with real database data
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="What exercises should I do?",
                agent_type=AgentType.WORKOUT,
                voice_mode=False,
                onboarding_mode=True
            )
            
            assert response is not None
            assert response.content == "Real database test response"
            
            # Verify agent was created
            mock_get_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_loading_with_profile(self, db_session: AsyncSession):
        """
        Test context loading with user profile.
        
        Verifies:
        - Context loader receives correct parameters
        - Profile data is loaded correctly
        - Requirements: 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create user with completed onboarding and profile
        user = User(
            id=uuid4(),
            email="context_test@example.com",
            hashed_password="hashed",
            full_name="Context Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9,
            is_complete=True,
            step_data={f"step_{i}": {"test": "data"} for i in range(1, 10)},
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="advanced",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        # Mock dependencies
        with patch('app.services.context_loader.load_agent_context') as mock_load_context, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "advanced"
            mock_context.user_profile = profile
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Response with profile context",
                agent_type="general",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query
            response = await orchestrator.route_query(
                user_id=str(user.id),
                query="Test query",
                agent_type=AgentType.GENERAL,
                voice_mode=False,
                onboarding_mode=False
            )
            
            assert response is not None
            
            # Verify context loader was called with correct parameters
            mock_load_context.assert_called_once()
            call_kwargs = mock_load_context.call_args[1]
            
            assert call_kwargs['user_id'] == str(user.id)
            assert call_kwargs['include_history'] == True
            assert call_kwargs['onboarding_mode'] == False
    
    @pytest.mark.asyncio
    async def test_missing_onboarding_state_error(self, db_session: AsyncSession):
        """
        Test error handling when onboarding state is missing.
        
        Verifies:
        - ValueError raised when onboarding state not found
        - Error message is helpful
        - Requirements: 5.2
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create user WITHOUT onboarding state
        user = User(
            id=uuid4(),
            email="no_onboarding@example.com",
            hashed_password="hashed",
            full_name="No Onboarding User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_load_context.return_value = mock_context
            
            # Try to route query without onboarding state
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="Test query",
                    agent_type=AgentType.WORKOUT,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            error_message = str(exc_info.value).lower()
            assert "onboarding state not found" in error_message
            assert str(user.id) in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
