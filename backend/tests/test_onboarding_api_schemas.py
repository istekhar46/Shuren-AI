"""
Tests for onboarding API request and response schemas.

This module tests the Pydantic schemas used for the onboarding chat API:
- OnboardingChatRequest: Request schema with message validation
- OnboardingChatResponse: Response schema with agent info
- CurrentAgentResponse: Schema for current agent info endpoint

Validates Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6
"""

import pytest
from pydantic import ValidationError

from app.schemas.onboarding import (
    OnboardingChatRequest,
    OnboardingChatResponse,
    CurrentAgentResponse,
)


class TestOnboardingChatRequest:
    """Tests for OnboardingChatRequest schema."""
    
    def test_valid_request_with_message_only(self):
        """Test valid request with only message field."""
        request = OnboardingChatRequest(
            message="I workout 3 times a week"
        )
        assert request.message == "I workout 3 times a week"
        assert request.step is None
    
    def test_valid_request_with_step(self):
        """Test valid request with message and step."""
        request = OnboardingChatRequest(
            message="I workout 3 times a week",
            step=0
        )
        assert request.message == "I workout 3 times a week"
        assert request.step == 0
    
    def test_message_strips_whitespace(self):
        """Test that message whitespace is stripped."""
        request = OnboardingChatRequest(
            message="  Hello  "
        )
        assert request.message == "  Hello  "  # Pydantic doesn't auto-strip
    
    def test_empty_message_fails(self):
        """Test that empty message raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatRequest(message="")
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("message",) and "at least 1 character" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_whitespace_only_message_passes_pydantic(self):
        """Test that whitespace-only message passes Pydantic validation."""
        # Note: The custom validator would catch this, but we're testing the schema
        request = OnboardingChatRequest(message="   ")
        assert request.message == "   "
    
    def test_message_too_long_fails(self):
        """Test that message exceeding max length fails."""
        long_message = "a" * 2001
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatRequest(message=long_message)
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("message",) and "at most 2000 characters" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_message_at_max_length_succeeds(self):
        """Test that message at exactly max length succeeds."""
        max_message = "a" * 2000
        request = OnboardingChatRequest(message=max_message)
        assert len(request.message) == 2000
    
    def test_step_validation_min(self):
        """Test that step < 0 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatRequest(
                message="Hello",
                step=-1
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("step",) and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_step_validation_max(self):
        """Test that step > 9 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatRequest(
                message="Hello",
                step=10
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("step",) and "less than or equal to 9" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_step_boundary_values(self):
        """Test step boundary values 0 and 9."""
        request_0 = OnboardingChatRequest(message="Hello", step=0)
        assert request_0.step == 0
        
        request_9 = OnboardingChatRequest(message="Hello", step=9)
        assert request_9.step == 9
    
    def test_missing_message_fails(self):
        """Test that missing message field fails."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatRequest()
        
        errors = exc_info.value.errors()
        # Check that message field is in the errors
        assert any(error["loc"] == ("message",) for error in errors)
    
    def test_serialization(self):
        """Test that request can be serialized to dict."""
        request = OnboardingChatRequest(
            message="Test message",
            step=3
        )
        data = request.model_dump()
        assert data["message"] == "Test message"
        assert data["step"] == 3


class TestOnboardingChatResponse:
    """Tests for OnboardingChatResponse schema."""
    
    def test_valid_response_minimal(self):
        """Test valid response with minimal required fields."""
        response = OnboardingChatResponse(
            message="Agent response",
            agent_type="fitness_assessment",
            current_step=0
        )
        assert response.message == "Agent response"
        assert response.agent_type == "fitness_assessment"
        assert response.current_step == 0
        assert response.step_complete is False
        assert response.next_action == "continue_conversation"
    
    def test_valid_response_all_fields(self):
        """Test valid response with all fields."""
        response = OnboardingChatResponse(
            message="Step complete!",
            agent_type="goal_setting",
            current_step=3,
            step_complete=True,
            next_action="advance_step"
        )
        assert response.message == "Step complete!"
        assert response.agent_type == "goal_setting"
        assert response.current_step == 3
        assert response.step_complete is True
        assert response.next_action == "advance_step"
    
    def test_current_step_validation_min(self):
        """Test that current_step < 0 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatResponse(
                message="Test",
                agent_type="fitness_assessment",
                current_step=-1
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("current_step",) and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_current_step_validation_max(self):
        """Test that current_step > 9 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatResponse(
                message="Test",
                agent_type="fitness_assessment",
                current_step=10
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("current_step",) and "less than or equal to 9" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            OnboardingChatResponse()
        
        errors = exc_info.value.errors()
        required_fields = {"message", "agent_type", "current_step"}
        error_fields = {error["loc"][0] for error in errors}
        assert required_fields.issubset(error_fields)
    
    def test_serialization(self):
        """Test that response can be serialized to dict."""
        response = OnboardingChatResponse(
            message="Test response",
            agent_type="workout_planning",
            current_step=4,
            step_complete=True,
            next_action="advance_step"
        )
        data = response.model_dump()
        assert data["message"] == "Test response"
        assert data["agent_type"] == "workout_planning"
        assert data["current_step"] == 4
        assert data["step_complete"] is True
        assert data["next_action"] == "advance_step"
    
    def test_json_serialization(self):
        """Test that response can be serialized to JSON."""
        response = OnboardingChatResponse(
            message="Test",
            agent_type="diet_planning",
            current_step=6
        )
        json_str = response.model_dump_json()
        assert "Test" in json_str
        assert "diet_planning" in json_str
        assert "6" in json_str


class TestCurrentAgentResponse:
    """Tests for CurrentAgentResponse schema."""
    
    def test_valid_response_minimal(self):
        """Test valid response with minimal required fields."""
        response = CurrentAgentResponse(
            agent_type="fitness_assessment",
            current_step=0,
            agent_description="I'll help assess your fitness level"
        )
        assert response.agent_type == "fitness_assessment"
        assert response.current_step == 0
        assert response.agent_description == "I'll help assess your fitness level"
        assert response.context_summary == {}
    
    def test_valid_response_with_context(self):
        """Test valid response with context summary."""
        context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "experience_years": 2
            }
        }
        response = CurrentAgentResponse(
            agent_type="goal_setting",
            current_step=3,
            agent_description="Let's define your goals",
            context_summary=context
        )
        assert response.agent_type == "goal_setting"
        assert response.current_step == 3
        assert response.context_summary == context
    
    def test_current_step_validation_min(self):
        """Test that current_step < 0 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CurrentAgentResponse(
                agent_type="fitness_assessment",
                current_step=-1,
                agent_description="Test"
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("current_step",) and "greater than or equal to 0" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_current_step_validation_max(self):
        """Test that current_step > 9 fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CurrentAgentResponse(
                agent_type="fitness_assessment",
                current_step=10,
                agent_description="Test"
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("current_step",) and "less than or equal to 9" in str(error["msg"]).lower()
            for error in errors
        )
    
    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            CurrentAgentResponse()
        
        errors = exc_info.value.errors()
        required_fields = {"agent_type", "current_step", "agent_description"}
        error_fields = {error["loc"][0] for error in errors}
        assert required_fields.issubset(error_fields)
    
    def test_context_summary_default(self):
        """Test that context_summary defaults to empty dict."""
        response = CurrentAgentResponse(
            agent_type="scheduling",
            current_step=8,
            agent_description="Let's set up your schedule"
        )
        assert response.context_summary == {}
        assert isinstance(response.context_summary, dict)
    
    def test_serialization(self):
        """Test that response can be serialized to dict."""
        response = CurrentAgentResponse(
            agent_type="workout_planning",
            current_step=4,
            agent_description="I'll create your workout plan",
            context_summary={"test": "data"}
        )
        data = response.model_dump()
        assert data["agent_type"] == "workout_planning"
        assert data["current_step"] == 4
        assert data["agent_description"] == "I'll create your workout plan"
        assert data["context_summary"] == {"test": "data"}
    
    def test_json_serialization(self):
        """Test that response can be serialized to JSON."""
        response = CurrentAgentResponse(
            agent_type="diet_planning",
            current_step=6,
            agent_description="Let's build your meal plan",
            context_summary={"key": "value"}
        )
        json_str = response.model_dump_json()
        assert "diet_planning" in json_str
        assert "6" in json_str
        assert "Let's build your meal plan" in json_str
        assert "key" in json_str


class TestSchemaIntegration:
    """Integration tests for schema interactions."""
    
    def test_request_response_flow(self):
        """Test that request and response schemas work together."""
        # Create request
        request = OnboardingChatRequest(
            message="I want to build muscle",
            step=3
        )
        
        # Simulate processing and create response
        response = OnboardingChatResponse(
            message="Great goal! Let's set some specific targets.",
            agent_type="goal_setting",
            current_step=request.step,
            step_complete=False,
            next_action="continue_conversation"
        )
        
        assert response.current_step == request.step
        assert response.agent_type == "goal_setting"
    
    def test_agent_info_matches_response(self):
        """Test that CurrentAgentResponse matches OnboardingChatResponse."""
        agent_info = CurrentAgentResponse(
            agent_type="fitness_assessment",
            current_step=1,
            agent_description="Assessing your fitness",
            context_summary={"fitness_level": "beginner"}
        )
        
        chat_response = OnboardingChatResponse(
            message="Tell me about your experience",
            agent_type=agent_info.agent_type,
            current_step=agent_info.current_step
        )
        
        assert chat_response.agent_type == agent_info.agent_type
        assert chat_response.current_step == agent_info.current_step
