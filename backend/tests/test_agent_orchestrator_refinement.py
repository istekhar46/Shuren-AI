"""
Unit and property tests for AgentOrchestrator refinement.

This module tests the enhanced access control method and related functionality
added as part of the agent orchestration refinement spec.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_orchestrator import AgentOrchestrator, AgentType
from app.models.user import User
from app.models.onboarding import OnboardingState
from unittest.mock import AsyncMock, MagicMock, patch
import logging


@pytest.mark.unit
class TestLogging:
    """Test logging functionality."""
    
    @pytest.mark.asyncio
    async def test_routing_decision_logged(self, db_session: AsyncSession, caplog):
        """All routing decisions should be logged with required fields."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user and onboarding state
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
        
        # Call _log_routing_decision
        with caplog.at_level(logging.INFO):
            orchestrator._log_routing_decision(
                user_id=str(user.id),
                agent_type=AgentType.WORKOUT,
                onboarding_mode=True,
                onboarding_state=onboarding_state,
                classification_used=True,
                routing_time_ms=45
            )
        
        # Verify log entry contains all required fields
        assert len(caplog.records) == 1
        log_message = caplog.records[0].message
        
        assert f"user={user.id}" in log_message
        assert "agent_type=workout" in log_message
        assert "onboarding_mode=True" in log_message
        assert "onboarding_complete=False" in log_message
        assert "onboarding_step=3/9" in log_message
        assert "mode=text" in log_message
        assert "classification_used=True" in log_message
        assert "routing_time_ms=45" in log_message
    
    @pytest.mark.asyncio
    async def test_access_violation_logged(self, db_session: AsyncSession, caplog):
        """Access control violations should be logged as warnings."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
        
        # Try to access onboarding mode with completed onboarding (should log warning)
        with caplog.at_level(logging.WARNING):
            with pytest.raises(ValueError):
                orchestrator._enforce_access_control(
                    user=user,
                    onboarding_state=onboarding_state,
                    agent_type=AgentType.WORKOUT,
                    onboarding_mode=True
                )
        
        # Verify warning was logged
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) >= 1
        
        log_message = warning_records[0].message
        assert "Access control violation" in log_message
        assert f"user={user.id}" in log_message
        assert "reason=onboarding_already_completed" in log_message
    
    @pytest.mark.asyncio
    async def test_performance_metrics_logged(self, db_session: AsyncSession, caplog):
        """Performance metrics should be included in logs."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
        
        # Mock the necessary methods to test route_query
        with patch.object(orchestrator, '_classify_query') as mock_classify, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent, \
             patch('app.services.context_loader.load_agent_context') as mock_load_context:
            
            # Setup mocks
            mock_classify.return_value = AgentType.WORKOUT
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            # Call route_query
            with caplog.at_level(logging.DEBUG):
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="What workout should I do?",
                    agent_type=None,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            # Verify performance metrics were logged
            debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
            
            # Should have logs for classification time, agent creation time, and performance metrics
            performance_logs = [r for r in debug_records if "time" in r.message.lower()]
            assert len(performance_logs) >= 1
            
            # Check for specific performance metrics
            perf_messages = [r.message for r in performance_logs]
            perf_text = " ".join(perf_messages)
            
            # Should log classification time, agent creation time, or total routing time
            assert any(
                keyword in perf_text.lower() 
                for keyword in ["classification", "agent_creation", "routing", "performance"]
            )


@pytest.mark.unit
class TestClassificationRefinement:
    """Test classification with onboarding_mode awareness."""
    
    @pytest.mark.asyncio
    async def test_classification_during_onboarding(self, db_session: AsyncSession):
        """Classification during onboarding returns specialized agents."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            # Test workout query
            mock_response = MagicMock()
            mock_response.content = "workout"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await orchestrator._classify_query(
                "What exercises should I do?",
                onboarding_mode=True
            )
            
            assert result == AgentType.WORKOUT
            
            # Verify the prompt used is for onboarding
            call_args = mock_llm.ainvoke.call_args[0][0]
            system_message = call_args[0].content
            assert "onboarding query" in system_message.lower()
            assert "fitness level" in system_message.lower()
            # Should NOT contain post-onboarding categories
            assert "tracker" not in system_message.lower()
            assert "general" not in system_message.lower()
    
    @pytest.mark.asyncio
    async def test_classification_post_onboarding(self, db_session: AsyncSession):
        """Classification post-onboarding returns any agent type."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            # Test general query
            mock_response = MagicMock()
            mock_response.content = "general"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await orchestrator._classify_query(
                "How are you today?",
                onboarding_mode=False
            )
            
            assert result == AgentType.GENERAL
            
            # Verify the prompt used is for post-onboarding
            call_args = mock_llm.ainvoke.call_args[0][0]
            system_message = call_args[0].content
            assert "fitness query" in system_message.lower()
            # Should contain all categories including tracker and general
            assert "tracker" in system_message.lower()
            assert "general" in system_message.lower()
    
    @pytest.mark.asyncio
    async def test_classification_cache_separation(self, db_session: AsyncSession):
        """Cache keys should be separate for different onboarding modes."""
        orchestrator = AgentOrchestrator(db_session, mode="voice")  # Voice mode enables caching
        
        query = "What should I eat?"
        
        # Mock the classifier LLM
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            # First call - onboarding mode
            mock_response_1 = MagicMock()
            mock_response_1.content = "diet"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response_1)
            
            result_1 = await orchestrator._classify_query(query, onboarding_mode=True)
            assert result_1 == AgentType.DIET
            first_call_count = mock_llm.ainvoke.call_count
            assert first_call_count == 1
            
            # Second call - same query, same mode (should use cache)
            result_2 = await orchestrator._classify_query(query, onboarding_mode=True)
            assert result_2 == AgentType.DIET
            assert mock_llm.ainvoke.call_count == first_call_count  # No additional call
            
            # Third call - same query, different mode (should NOT use cache, makes new call)
            mock_response_2 = MagicMock()
            mock_response_2.content = "general"
            # Reset the mock to track new calls
            mock_llm.ainvoke.reset_mock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response_2)
            
            result_3 = await orchestrator._classify_query(query, onboarding_mode=False)
            assert result_3 == AgentType.GENERAL
            assert mock_llm.ainvoke.call_count == 1  # New call made
    
    @pytest.mark.asyncio
    async def test_classification_default_during_onboarding(self, db_session: AsyncSession):
        """Unknown classification during onboarding defaults to WORKOUT."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to return unknown type
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            mock_response = MagicMock()
            mock_response.content = "unknown_type"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await orchestrator._classify_query(
                "Some query",
                onboarding_mode=True
            )
            
            assert result == AgentType.WORKOUT
    
    @pytest.mark.asyncio
    async def test_classification_default_post_onboarding(self, db_session: AsyncSession):
        """Unknown classification post-onboarding defaults to GENERAL."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to return unknown type
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            mock_response = MagicMock()
            mock_response.content = "unknown_type"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await orchestrator._classify_query(
                "Some query",
                onboarding_mode=False
            )
            
            assert result == AgentType.GENERAL
    
    @pytest.mark.asyncio
    async def test_classification_exception_handling_onboarding(self, db_session: AsyncSession):
        """Exception during classification in onboarding mode defaults to WORKOUT."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to raise exception
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
            
            result = await orchestrator._classify_query(
                "Some query",
                onboarding_mode=True
            )
            
            assert result == AgentType.WORKOUT
    
    @pytest.mark.asyncio
    async def test_classification_exception_handling_post_onboarding(self, db_session: AsyncSession):
        """Exception during classification post-onboarding defaults to GENERAL."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to raise exception
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            mock_llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))
            
            result = await orchestrator._classify_query(
                "Some query",
                onboarding_mode=False
            )
            
            assert result == AgentType.GENERAL


@pytest.mark.property
class TestClassificationModeConsistency:
    """Property-based tests for classification mode consistency."""
    
    @given(
        onboarding_mode=st.booleans(),
        query=st.text(min_size=1, max_size=100)
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
        max_examples=30  # Reduced for faster execution
    )
    @pytest.mark.asyncio
    async def test_property_classification_mode_consistency(
        self,
        onboarding_mode: bool,
        query: str,
        db_session: AsyncSession
    ):
        """
        Property: Classification Mode Consistency
        
        **Validates: Requirements 3.5**
        
        For any query and onboarding_mode, verify classification returns appropriate agent types:
        
        During Onboarding (onboarding_mode=True):
        - Classification should return one of: WORKOUT, DIET, SCHEDULER, SUPPLEMENT
        - Should NEVER return: GENERAL, TRACKER
        - TEST agent is allowed but not expected from classification
        
        Post-Onboarding (onboarding_mode=False):
        - Classification can return any agent type
        - Defaults to GENERAL on errors
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to return various agent types
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            # Test with valid agent type response
            if onboarding_mode:
                # During onboarding - return a specialized agent
                mock_response = MagicMock()
                mock_response.content = "workout"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            else:
                # Post-onboarding - can return any agent
                mock_response = MagicMock()
                mock_response.content = "general"
                mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            try:
                result = await orchestrator._classify_query(query, onboarding_mode)
                
                # Verify result is a valid AgentType
                assert isinstance(result, AgentType)
                
                # Verify mode-specific constraints
                specialized_agents = {
                    AgentType.WORKOUT,
                    AgentType.DIET,
                    AgentType.SCHEDULER,
                    AgentType.SUPPLEMENT
                }
                
                if onboarding_mode:
                    # During onboarding: should return specialized agent or default to WORKOUT
                    assert result in specialized_agents or result == AgentType.TEST, (
                        f"During onboarding, classification should return specialized agent. "
                        f"Got: {result.value}"
                    )
                else:
                    # Post-onboarding: can return any agent type
                    assert result in AgentType, (
                        f"Classification should return valid AgentType. Got: {result.value}"
                    )
                
            except Exception as e:
                # If exception occurs, verify default behavior
                pytest.fail(f"Classification raised unexpected exception: {e}")
    
    @given(
        onboarding_mode=st.booleans()
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
        max_examples=20
    )
    @pytest.mark.asyncio
    async def test_property_classification_error_defaults(
        self,
        onboarding_mode: bool,
        db_session: AsyncSession
    ):
        """
        Property: Classification Error Defaults
        
        **Validates: Requirements 3.5**
        
        When classification fails or returns unknown type:
        - During onboarding: defaults to WORKOUT
        - Post-onboarding: defaults to GENERAL
        """
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Mock the classifier LLM to return unknown type
        with patch.object(orchestrator, '_init_classifier_llm') as mock_init:
            mock_llm = AsyncMock()
            mock_init.return_value = mock_llm
            
            mock_response = MagicMock()
            mock_response.content = "unknown_invalid_type"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            result = await orchestrator._classify_query(
                "test query",
                onboarding_mode
            )
            
            # Verify default based on mode
            if onboarding_mode:
                assert result == AgentType.WORKOUT, (
                    f"During onboarding, unknown classification should default to WORKOUT. "
                    f"Got: {result.value}"
                )
            else:
                assert result == AgentType.GENERAL, (
                    f"Post-onboarding, unknown classification should default to GENERAL. "
                    f"Got: {result.value}"
                )


@pytest.mark.property
class TestAccessControlConsistency:
    """Property-based tests for access control consistency."""
    
    @given(
        onboarding_complete=st.booleans(),
        onboarding_mode=st.booleans(),
        agent_type=st.sampled_from([
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SUPPLEMENT,
            AgentType.SCHEDULER,
            AgentType.GENERAL,
            AgentType.TRACKER,
            AgentType.TEST
        ])
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
        max_examples=50  # Reduced for faster execution
    )
    @pytest.mark.asyncio
    async def test_property_access_control_consistency(
        self,
        onboarding_complete: bool,
        onboarding_mode: bool,
        agent_type: AgentType,
        db_session: AsyncSession
    ):
        """
        Property: Access Control Consistency
        
        **Validates: Requirements 2.1.1-2.1.6, 2.2.1-2.2.3**
        
        For any combination of onboarding_complete, onboarding_mode, and agent_type,
        verify consistent access control decisions according to the rules:
        
        During Onboarding (onboarding_mode=True):
        - Specialized agents (WORKOUT, DIET, SCHEDULER, SUPPLEMENT): ✅ Allowed
        - General agent: ❌ Blocked
        - Tracker agent: ❌ Blocked
        - Test agent: ✅ Allowed
        - If onboarding already complete: ❌ Blocked (all agents)
        
        Post-Onboarding (onboarding_mode=False):
        - Specialized agents: ❌ Blocked
        - General agent: ✅ Allowed
        - Tracker agent: ✅ Allowed
        - Test agent: ✅ Allowed
        - If onboarding not complete: ❌ Blocked (all agents)
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
        
        # Create onboarding state
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=9 if onboarding_complete else 3,
            is_complete=onboarding_complete,
            step_data={} if not onboarding_complete else {
                f"step_{i}": {"test": "data"} for i in range(1, 10)
            },
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        
        await db_session.commit()
        await db_session.refresh(user)
        await db_session.refresh(onboarding_state)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Define specialized agents
        specialized_agents = {
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SCHEDULER,
            AgentType.SUPPLEMENT
        }
        
        # Determine expected behavior
        should_raise_error = False
        expected_error_keywords = []
        
        if onboarding_mode:
            # During onboarding
            if onboarding_complete:
                # Reject: onboarding already completed
                should_raise_error = True
                expected_error_keywords = ["already completed", "regular chat"]
            elif agent_type == AgentType.GENERAL:
                # Reject: general agent not available during onboarding
                should_raise_error = True
                expected_error_keywords = ["general agent", "not available", "onboarding"]
            elif agent_type == AgentType.TRACKER:
                # Reject: tracker agent not available during onboarding
                should_raise_error = True
                expected_error_keywords = ["tracker agent", "not available", "onboarding"]
            # else: Allow (specialized agents and test agent)
        else:
            # Post-onboarding
            if not onboarding_complete:
                # Reject: onboarding not completed
                should_raise_error = True
                expected_error_keywords = ["complete onboarding", "onboarding first"]
            elif agent_type in specialized_agents:
                # Reject: specialized agents not available post-onboarding
                should_raise_error = True
                expected_error_keywords = ["specialized agent", "not available", "after onboarding"]
            # else: Allow (general, tracker, test agents)
        
        # Test the access control
        if should_raise_error:
            with pytest.raises(ValueError) as exc_info:
                orchestrator._enforce_access_control(
                    user=user,
                    onboarding_state=onboarding_state,
                    agent_type=agent_type,
                    onboarding_mode=onboarding_mode
                )
            
            # Verify error message contains expected keywords
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in expected_error_keywords), (
                f"Error message should contain one of {expected_error_keywords}. "
                f"Got: {exc_info.value}"
            )
        else:
            # Should not raise error
            try:
                orchestrator._enforce_access_control(
                    user=user,
                    onboarding_state=onboarding_state,
                    agent_type=agent_type,
                    onboarding_mode=onboarding_mode
                )
                # Success - no error raised
            except ValueError as e:
                pytest.fail(
                    f"Access control raised error for allowed case. "
                    f"onboarding_complete={onboarding_complete}, "
                    f"onboarding_mode={onboarding_mode}, "
                    f"agent_type={agent_type.value}, "
                    f"Error: {e}"
                )


@pytest.mark.unit
class TestRouteQueryUpdates:
    """Test route_query method updates."""
    
    @pytest.mark.asyncio
    async def test_access_control_is_enforced(self, db_session: AsyncSession):
        """Test that access control is enforced in route_query."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
        
        # Mock context loader
        with patch('app.services.context_loader.load_agent_context') as mock_load_context:
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            # Try to access onboarding mode with completed onboarding (should raise error)
            with pytest.raises(ValueError) as exc_info:
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="What workout should I do?",
                    agent_type=AgentType.WORKOUT,
                    voice_mode=False,
                    onboarding_mode=True  # Invalid: onboarding already completed
                )
            
            assert "already completed" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_classification_receives_onboarding_mode(self, db_session: AsyncSession):
        """Test that classification receives onboarding_mode parameter."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
             patch.object(orchestrator, '_classify_query') as mock_classify, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            mock_classify.return_value = AgentType.WORKOUT
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query without explicit agent_type (triggers classification)
            await orchestrator.route_query(
                user_id=str(user.id),
                query="What workout should I do?",
                agent_type=None,  # Will trigger classification
                voice_mode=False,
                onboarding_mode=True
            )
            
            # Verify _classify_query was called with onboarding_mode=True
            mock_classify.assert_called_once()
            call_args = mock_classify.call_args
            assert call_args[0][1] == True  # Second positional arg is onboarding_mode
    
    @pytest.mark.asyncio
    async def test_general_agent_forced_post_onboarding(self, db_session: AsyncSession, caplog):
        """Test that GENERAL agent is forced post-onboarding."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
             patch.object(orchestrator, '_classify_query') as mock_classify, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            # Classification returns WORKOUT (but should be overridden to GENERAL)
            mock_classify.return_value = AgentType.WORKOUT
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="general",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query post-onboarding
            with caplog.at_level(logging.INFO):
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="What workout should I do?",
                    agent_type=None,  # Will classify as WORKOUT
                    voice_mode=False,
                    onboarding_mode=False  # Post-onboarding
                )
            
            # Verify agent was created with GENERAL type (not WORKOUT)
            mock_get_agent.assert_called_once()
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.GENERAL
            
            # Verify override was logged
            log_messages = [r.message for r in caplog.records if r.levelname == "INFO"]
            assert any("forcing to general agent" in msg.lower() for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_test_agent_not_forced_post_onboarding(self, db_session: AsyncSession):
        """Test that TEST agent is NOT forced to GENERAL post-onboarding."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with completed onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="test",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query with TEST agent
            await orchestrator.route_query(
                user_id=str(user.id),
                query="Test query",
                agent_type=AgentType.TEST,
                voice_mode=False,
                onboarding_mode=False
            )
            
            # Verify agent was created with TEST type (not forced to GENERAL)
            mock_get_agent.assert_called_once()
            call_args = mock_get_agent.call_args[0]
            assert call_args[0] == AgentType.TEST
    
    @pytest.mark.asyncio
    async def test_routing_decision_is_logged(self, db_session: AsyncSession, caplog):
        """Test that routing decision is logged."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query
            with caplog.at_level(logging.INFO):
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="What workout should I do?",
                    agent_type=AgentType.WORKOUT,
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            # Verify routing decision was logged
            info_records = [r for r in caplog.records if r.levelname == "INFO"]
            routing_logs = [r for r in info_records if "agent routing" in r.message.lower()]
            
            assert len(routing_logs) >= 1
            log_message = routing_logs[0].message
            
            # Verify log contains required fields
            assert f"user={user.id}" in log_message
            assert "agent_type=workout" in log_message
            assert "onboarding_mode=True" in log_message
    
    @pytest.mark.asyncio
    async def test_performance_timing_is_recorded(self, db_session: AsyncSession, caplog):
        """Test that performance timing is recorded."""
        orchestrator = AgentOrchestrator(db_session, mode="text")
        
        # Create test user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
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
             patch.object(orchestrator, '_classify_query') as mock_classify, \
             patch.object(orchestrator, '_get_or_create_agent') as mock_get_agent:
            
            mock_context = MagicMock()
            mock_context.fitness_level = "beginner"
            mock_load_context.return_value = mock_context
            
            mock_classify.return_value = AgentType.WORKOUT
            
            mock_agent = AsyncMock()
            mock_agent.process_text = AsyncMock(return_value=MagicMock(
                content="Test response",
                agent_type="workout",
                tools_used=[],
                metadata={}
            ))
            mock_get_agent.return_value = mock_agent
            
            # Call route_query
            with caplog.at_level(logging.DEBUG):
                await orchestrator.route_query(
                    user_id=str(user.id),
                    query="What workout should I do?",
                    agent_type=None,  # Triggers classification
                    voice_mode=False,
                    onboarding_mode=True
                )
            
            # Verify performance timing was logged
            debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
            
            # Should have logs for timing
            timing_logs = [r for r in debug_records if "time" in r.message.lower()]
            assert len(timing_logs) >= 1
            
            # Check for specific timing metrics
            timing_messages = " ".join([r.message for r in timing_logs])
            assert any(
                keyword in timing_messages.lower()
                for keyword in ["classification", "agent_creation", "routing", "performance"]
            )
            
            # Verify routing_time_ms is in the routing decision log
            info_records = [r for r in caplog.records if r.levelname == "INFO"]
            routing_logs = [r for r in info_records if "agent routing" in r.message.lower()]
            
            if routing_logs:
                assert "routing_time_ms" in routing_logs[0].message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
