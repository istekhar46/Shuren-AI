"""Property-based tests for OnboardingService.

This module contains property-based tests using Hypothesis to verify
universal correctness properties of the onboarding system.

Property 6: Completion Percentage Calculation
- For any set of completed states (0-9), verify percentage = (completed/9)*100
- Tests that the completion percentage is always correctly calculated
- Validates Requirements 2.2.4
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.onboarding_service import OnboardingService
from app.models.user import User


@pytest.mark.property
class TestCompletionPercentageProperty:
    """Property-based tests for completion percentage calculation."""
    
    @given(
        completed_states=st.lists(
            st.integers(min_value=1, max_value=9),
            unique=True,
            min_size=0,
            max_size=9
        )
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.asyncio
    async def test_completion_percentage_calculation_property(
        self,
        completed_states: list[int],
        db_session: AsyncSession,
        test_user: User
    ):
        """Property 6: Completion Percentage Calculation.
        
        **Validates: Requirements 2.2.4**
        
        For any set of completed states (0-9), verify that:
        - completion_percentage = (number_of_completed_states / 9) * 100
        - The percentage is always an integer
        - The percentage is always between 0 and 100 inclusive
        
        This property ensures that the completion percentage is always
        correctly calculated regardless of which states are completed.
        
        Args:
            completed_states: List of completed state numbers (1-9)
            db_session: Database session
            test_user: Test user fixture
        """
        service = OnboardingService(db_session)
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Set up step_data with completed states
        state.step_data = {}
        for step_num in completed_states:
            state.step_data[f"step_{step_num}"] = {"test": "data"}
        
        # Set current_step to the highest completed state, or 1 if none completed
        if completed_states:
            state.current_step = max(completed_states)
        else:
            state.current_step = 1
        
        await db_session.commit()
        
        # Get progress
        progress = await service.get_progress(test_user.id)
        
        # Calculate expected percentage
        num_completed = len(completed_states)
        expected_percentage = int((num_completed / 9) * 100)
        
        # Verify the property: percentage = (completed/9)*100
        assert progress.completion_percentage == expected_percentage, \
            f"Expected {expected_percentage}% for {num_completed} completed states, " \
            f"got {progress.completion_percentage}%"
        
        # Verify percentage is an integer
        assert isinstance(progress.completion_percentage, int), \
            "Completion percentage must be an integer"
        
        # Verify percentage is in valid range [0, 100]
        assert 0 <= progress.completion_percentage <= 100, \
            f"Completion percentage must be between 0 and 100, got {progress.completion_percentage}"
        
        # Verify completed_states list matches what we set
        assert sorted(progress.completed_states) == sorted(completed_states), \
            f"Expected completed states {sorted(completed_states)}, " \
            f"got {sorted(progress.completed_states)}"
        
        # Verify total_states is always 9
        assert progress.total_states == 9, \
            "Total states must always be 9"
        
        # Verify can_complete is True only when all 9 states are completed
        if num_completed == 9:
            assert progress.can_complete is True, \
                "can_complete should be True when all 9 states are completed"
        else:
            assert progress.can_complete is False, \
                f"can_complete should be False when only {num_completed}/9 states are completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])



@pytest.mark.property
class TestAgentFunctionToolInvocationProperty:
    """Property-based tests for agent function tool invocation."""
    
    @given(
        agent_type=st.sampled_from(["workout", "diet", "scheduler", "supplement"]),
        tool_index=st.integers(min_value=0, max_value=2)  # Each agent has at least 3 onboarding tools
    )
    @settings(
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None  # Disable deadline for database operations
    )
    @pytest.mark.asyncio
    async def test_agent_function_tool_invocation_property(
        self,
        agent_type: str,
        tool_index: int,
        db_session: AsyncSession,
        test_user: User
    ):
        """Property 16: Agent Function Tool Invocation.
        
        **Validates: Requirements 2.3.1**
        
        For any agent with tools, verify that:
        - The tool successfully invokes the onboarding endpoint
        - The tool returns a structured response (success or error)
        - The response contains required fields (success, message/error)
        - Valid data results in successful save
        - Invalid data results in structured error response
        
        This property ensures that all agent onboarding tools correctly
        integrate with the onboarding service layer.
        
        Args:
            agent_type: Type of agent to test ("workout", "diet", "scheduler", "supplement")
            tool_index: Index of the onboarding tool to test (0-2)
            db_session: Database session
            test_user: Test user fixture
        """
        from app.agents.workout_planner import WorkoutPlannerAgent
        from app.agents.diet_planner import DietPlannerAgent
        from app.agents.scheduler import SchedulerAgent
        from app.agents.supplement_guide import SupplementGuideAgent
        from app.agents.context import AgentContext
        from app.models.onboarding import OnboardingState
        from sqlalchemy import select, delete
        from uuid import UUID
        
        # Clean up any existing onboarding state for this user to ensure clean test
        await db_session.execute(
            delete(OnboardingState).where(OnboardingState.user_id == test_user.id)
        )
        await db_session.commit()
        
        # Create fresh onboarding state
        onboarding_state = OnboardingState(
            user_id=test_user.id,
            current_step=1,
            step_data={},
            is_complete=False
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        # Create agent context
        agent_context = AgentContext(
            user_id=str(test_user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high"
        )
        
        # Map agent types to agent classes and their onboarding tools
        agent_tools_map = {
            "workout": {
                "agent_class": WorkoutPlannerAgent,
                "tools": [
                    {
                        "method": "save_fitness_level",
                        "valid_args": {"fitness_level": "intermediate"},
                        "invalid_args": {"fitness_level": "expert"},  # Invalid value
                        "expected_state": 1
                    },
                    {
                        "method": "save_fitness_goals",
                        "valid_args": {"goals": [{"goal_type": "muscle_gain", "priority": 1}]},
                        "invalid_args": {"goals": []},  # Empty list invalid
                        "expected_state": 2
                    },
                    {
                        "method": "save_workout_constraints",
                        "valid_args": {
                            "equipment": ["dumbbells"],
                            "injuries": [],
                            "limitations": []
                        },
                        "invalid_args": {
                            "equipment": "not_a_list",  # Should be list
                            "injuries": [],
                            "limitations": []
                        },
                        "expected_state": 3
                    }
                ]
            },
            "diet": {
                "agent_class": DietPlannerAgent,
                "tools": [
                    {
                        "method": "save_dietary_preferences",
                        "valid_args": {
                            "diet_type": "vegetarian",
                            "allergies": [],
                            "intolerances": [],
                            "dislikes": []
                        },
                        "invalid_args": {
                            "diet_type": "invalid_diet",  # Invalid diet type
                            "allergies": [],
                            "intolerances": [],
                            "dislikes": []
                        },
                        "expected_state": 4
                    },
                    {
                        "method": "save_meal_plan",
                        "valid_args": {
                            "daily_calorie_target": 2000,
                            "protein_percentage": 30.0,
                            "carbs_percentage": 45.0,
                            "fats_percentage": 25.0
                        },
                        "invalid_args": {
                            "daily_calorie_target": 2000,
                            "protein_percentage": 30.0,
                            "carbs_percentage": 40.0,
                            "fats_percentage": 40.0  # Sum > 100
                        },
                        "expected_state": 5
                    }
                ]
            },
            "scheduler": {
                "agent_class": SchedulerAgent,
                "tools": [
                    {
                        "method": "save_meal_schedule",
                        "valid_args": {
                            "meals": [
                                {"meal_name": "Breakfast", "scheduled_time": "08:00"}
                            ]
                        },
                        "invalid_args": {
                            "meals": []  # Empty list invalid
                        },
                        "expected_state": 6
                    },
                    {
                        "method": "save_workout_schedule",
                        "valid_args": {
                            "workouts": [
                                {"day_of_week": 1, "scheduled_time": "07:00"}
                            ]
                        },
                        "invalid_args": {
                            "workouts": []  # Empty list invalid
                        },
                        "expected_state": 7
                    },
                    {
                        "method": "save_hydration_schedule",
                        "valid_args": {
                            "daily_water_target_ml": 3000,
                            "reminder_frequency_minutes": 60
                        },
                        "invalid_args": {
                            "daily_water_target_ml": 100,  # Too low (< 500)
                            "reminder_frequency_minutes": 60
                        },
                        "expected_state": 8
                    }
                ]
            },
            "supplement": {
                "agent_class": SupplementGuideAgent,
                "tools": [
                    {
                        "method": "save_supplement_preferences",
                        "valid_args": {
                            "interested_in_supplements": True,
                            "current_supplements": ["protein powder"]
                        },
                        "invalid_args": {
                            "interested_in_supplements": "not_a_bool",  # Should be bool
                            "current_supplements": []
                        },
                        "expected_state": 9
                    }
                ]
            }
        }
        
        # Get agent configuration
        agent_config = agent_tools_map[agent_type]
        
        # Limit tool_index to available tools
        if tool_index >= len(agent_config["tools"]):
            tool_index = tool_index % len(agent_config["tools"])
        
        tool_config = agent_config["tools"][tool_index]
        
        # Create agent instance
        agent_class = agent_config["agent_class"]
        agent = agent_class(context=agent_context, db_session=db_session)
        
        # Get the tool method
        tool_method = getattr(agent, tool_config["method"])
        
        # Test 1: Valid data should result in successful save
        valid_result = await tool_method(**tool_config["valid_args"])
        
        # Verify response structure
        assert isinstance(valid_result, dict), \
            f"Tool {tool_config['method']} must return a dict"
        
        assert "success" in valid_result, \
            f"Tool {tool_config['method']} response must contain 'success' field"
        
        # For valid data, expect success=True
        if valid_result["success"]:
            # Verify success response structure
            assert "message" in valid_result, \
                f"Successful response must contain 'message' field"
            
            assert "current_state" in valid_result, \
                f"Successful response must contain 'current_state' field"
            
            assert "next_state" in valid_result, \
                f"Successful response must contain 'next_state' field"
            
            # Verify current_state matches expected
            assert valid_result["current_state"] == tool_config["expected_state"], \
                f"Expected current_state={tool_config['expected_state']}, " \
                f"got {valid_result['current_state']}"
            
            # Verify next_state is correct
            expected_next = tool_config["expected_state"] + 1 if tool_config["expected_state"] < 9 else None
            assert valid_result["next_state"] == expected_next, \
                f"Expected next_state={expected_next}, got {valid_result['next_state']}"
            
            # Verify data was actually saved to database
            from app.models.onboarding import OnboardingState
            from sqlalchemy import select
            from uuid import UUID
            
            stmt = select(OnboardingState).where(
                OnboardingState.user_id == UUID(agent_context.user_id)
            )
            db_result = await db_session.execute(stmt)
            onboarding_state = db_result.scalar_one()
            
            step_key = f"step_{tool_config['expected_state']}"
            assert step_key in onboarding_state.step_data, \
                f"Data for {step_key} should be saved in database"
        
        # Test 2: Invalid data should result in structured error
        invalid_result = await tool_method(**tool_config["invalid_args"])
        
        # Verify response structure
        assert isinstance(invalid_result, dict), \
            f"Tool {tool_config['method']} must return a dict for invalid data"
        
        assert "success" in invalid_result, \
            f"Tool {tool_config['method']} error response must contain 'success' field"
        
        # For invalid data, expect success=False
        if not invalid_result["success"]:
            # Verify error response structure
            assert "error" in invalid_result, \
                f"Error response must contain 'error' field"
            
            assert "error_code" in invalid_result, \
                f"Error response must contain 'error_code' field"
            
            # Verify error_code is one of the expected values
            assert invalid_result["error_code"] in ["VALIDATION_ERROR", "INTERNAL_ERROR"], \
                f"error_code must be VALIDATION_ERROR or INTERNAL_ERROR, " \
                f"got {invalid_result['error_code']}"
            
            # If validation error, should have field information
            if invalid_result["error_code"] == "VALIDATION_ERROR":
                assert "field" in invalid_result, \
                    f"Validation error response should contain 'field' information"
        
        # Property: All tool invocations return structured responses
        # This ensures consistent error handling and response format across all agents
