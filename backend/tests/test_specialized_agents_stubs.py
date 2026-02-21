"""
Tests for specialized onboarding agent stub implementations.

These tests verify that all five specialized agents can be instantiated
and implement the required abstract methods from BaseOnboardingAgent.
"""

import pytest
from uuid import uuid4
from unittest.mock import patch

from app.agents.onboarding import (
    FitnessAssessmentAgent,
    GoalSettingAgent,
    WorkoutPlanningAgent,
    DietPlanningAgent,
    SchedulingAgent,
)
from app.schemas.onboarding import AgentResponse


@pytest.mark.unit
class TestFitnessAssessmentAgentStub:
    """Test FitnessAssessmentAgent stub implementation."""
    
    def test_agent_type_is_set(self, db_session):
        """Test that agent_type is correctly set."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = FitnessAssessmentAgent(db_session, {})
            assert agent.agent_type == "fitness_assessment"
    
    async def test_process_message_returns_response(self, db_session):
        """Test that process_message returns AgentResponse."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = FitnessAssessmentAgent(db_session, {})
            response = await agent.process_message("test message", uuid4())
            
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "fitness_assessment"
            assert response.step_complete is False
            assert response.next_action == "continue_conversation"
    
    def test_get_tools_returns_list(self, db_session):
        """Test that get_tools returns a list."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = FitnessAssessmentAgent(db_session, {})
            tools = agent.get_tools()
            
            assert isinstance(tools, list)
            assert len(tools) == 0  # Stub returns empty list
    
    def test_get_system_prompt_returns_string(self, db_session):
        """Test that get_system_prompt returns a non-empty string."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = FitnessAssessmentAgent(db_session, {})
            prompt = agent.get_system_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Fitness Assessment Agent" in prompt


@pytest.mark.unit
class TestGoalSettingAgentStub:
    """Test GoalSettingAgent stub implementation."""
    
    def test_agent_type_is_set(self, db_session):
        """Test that agent_type is correctly set."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = GoalSettingAgent(db_session, {})
            assert agent.agent_type == "goal_setting"
    
    async def test_process_message_returns_response(self, db_session):
        """Test that process_message returns AgentResponse."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = GoalSettingAgent(db_session, {})
            response = await agent.process_message("test message", uuid4())
            
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "goal_setting"
            assert response.step_complete is False
            assert response.next_action == "continue_conversation"
    
    def test_get_tools_returns_list(self, db_session):
        """Test that get_tools returns a list."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = GoalSettingAgent(db_session, {})
            tools = agent.get_tools()
            
            assert isinstance(tools, list)
            assert len(tools) == 0
    
    def test_get_system_prompt_returns_string(self, db_session):
        """Test that get_system_prompt returns a non-empty string."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = GoalSettingAgent(db_session, {})
            prompt = agent.get_system_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Goal Setting Agent" in prompt


@pytest.mark.unit
class TestWorkoutPlanningAgentStub:
    """Test WorkoutPlanningAgent stub implementation."""
    
    def test_agent_type_is_set(self, db_session):
        """Test that agent_type is correctly set."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = WorkoutPlanningAgent(db_session, {})
            assert agent.agent_type == "workout_planning"
    
    async def test_process_message_returns_response(self, db_session):
        """Test that process_message returns AgentResponse."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = WorkoutPlanningAgent(db_session, {})
            response = await agent.process_message("test message", uuid4())
            
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "workout_planning"
            assert response.step_complete is False
            assert response.next_action == "continue_conversation"
    
    def test_get_tools_returns_list(self, db_session):
        """Test that get_tools returns a list."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = WorkoutPlanningAgent(db_session, {})
            tools = agent.get_tools()
            
            assert isinstance(tools, list)
            assert len(tools) == 0
    
    def test_get_system_prompt_returns_string(self, db_session):
        """Test that get_system_prompt returns a non-empty string."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = WorkoutPlanningAgent(db_session, {})
            prompt = agent.get_system_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Workout Planning Agent" in prompt


@pytest.mark.unit
class TestDietPlanningAgentStub:
    """Test DietPlanningAgent stub implementation."""
    
    def test_agent_type_is_set(self, db_session):
        """Test that agent_type is correctly set."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = DietPlanningAgent(db_session, {})
            assert agent.agent_type == "diet_planning"
    
    async def test_process_message_returns_response(self, db_session):
        """Test that process_message returns AgentResponse."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = DietPlanningAgent(db_session, {})
            response = await agent.process_message("test message", uuid4())
            
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "diet_planning"
            assert response.step_complete is False
            assert response.next_action == "continue_conversation"
    
    def test_get_tools_returns_list(self, db_session):
        """Test that get_tools returns a list."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = DietPlanningAgent(db_session, {})
            tools = agent.get_tools()
            
            assert isinstance(tools, list)
            assert len(tools) == 0
    
    def test_get_system_prompt_returns_string(self, db_session):
        """Test that get_system_prompt returns a non-empty string."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = DietPlanningAgent(db_session, {})
            prompt = agent.get_system_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Diet Planning Agent" in prompt


@pytest.mark.unit
class TestSchedulingAgentStub:
    """Test SchedulingAgent stub implementation."""
    
    def test_agent_type_is_set(self, db_session):
        """Test that agent_type is correctly set."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = SchedulingAgent(db_session, {})
            assert agent.agent_type == "scheduling"
    
    async def test_process_message_returns_response(self, db_session):
        """Test that process_message returns AgentResponse."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = SchedulingAgent(db_session, {})
            response = await agent.process_message("test message", uuid4())
            
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "scheduling"
            assert response.step_complete is False
            assert response.next_action == "continue_conversation"
    
    def test_get_tools_returns_list(self, db_session):
        """Test that get_tools returns a list."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = SchedulingAgent(db_session, {})
            tools = agent.get_tools()
            
            assert isinstance(tools, list)
            assert len(tools) == 0
    
    def test_get_system_prompt_returns_string(self, db_session):
        """Test that get_system_prompt returns a non-empty string."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = SchedulingAgent(db_session, {})
            prompt = agent.get_system_prompt()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert "Scheduling Agent" in prompt


@pytest.mark.unit
class TestAllAgentsImplementAbstractMethods:
    """Test that all agents properly implement abstract methods."""
    
    @pytest.mark.parametrize("agent_class,expected_type", [
        (FitnessAssessmentAgent, "fitness_assessment"),
        (GoalSettingAgent, "goal_setting"),
        (WorkoutPlanningAgent, "workout_planning"),
        (DietPlanningAgent, "diet_planning"),
        (SchedulingAgent, "scheduling"),
    ])
    def test_agent_can_be_instantiated(self, db_session, agent_class, expected_type):
        """Test that each agent can be instantiated without errors."""
        with patch('app.agents.onboarding.base.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            agent = agent_class(db_session, {})
            assert agent.agent_type == expected_type
            assert hasattr(agent, 'process_message')
            assert hasattr(agent, 'get_tools')
            assert hasattr(agent, 'get_system_prompt')
            assert hasattr(agent, 'save_context')
            assert hasattr(agent, 'llm')
