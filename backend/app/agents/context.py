"""
Agent context models for the Shuren AI fitness coaching system.

This module defines immutable context objects that contain all user data
needed for agent interactions, eliminating the need for repeated database queries.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """
    Immutable context passed to all agents containing user data and state.
    
    This context is loaded once per interaction and provides agents with
    all necessary information to make informed decisions without additional
    database queries.
    
    Attributes:
        user_id: Unique identifier for the user
        fitness_level: User's current fitness level (beginner/intermediate/advanced)
        primary_goal: User's main fitness objective (fat_loss/muscle_gain/general_fitness)
        secondary_goal: Optional secondary fitness objective
        energy_level: User's current energy state (low/medium/high)
        current_workout_plan: Cached workout plan data from database
        current_meal_plan: Cached meal plan data from database
        conversation_history: Recent conversation messages for context
        loaded_at: Timestamp when this context was loaded
    """
    
    # User Identity
    user_id: str = Field(
        ...,
        description="Unique identifier for the user"
    )
    
    # Fitness Profile
    fitness_level: str = Field(
        ...,
        description="User's current fitness level: 'beginner', 'intermediate', or 'advanced'"
    )
    
    primary_goal: str = Field(
        ...,
        description="User's main fitness objective: 'fat_loss', 'muscle_gain', or 'general_fitness'"
    )
    
    secondary_goal: Optional[str] = Field(
        default=None,
        description="Optional secondary fitness objective"
    )
    
    # Current State
    energy_level: str = Field(
        default="medium",
        description="User's current energy state: 'low', 'medium', or 'high'"
    )
    
    # Plans (cached from database)
    current_workout_plan: Dict = Field(
        default_factory=dict,
        description="Cached workout plan data from database"
    )
    
    current_meal_plan: Dict = Field(
        default_factory=dict,
        description="Cached meal plan data from database"
    )
    
    # Conversation History
    conversation_history: List[Dict] = Field(
        default_factory=list,
        description="Recent conversation messages for context (limited to last N messages)"
    )
    
    # Metadata
    loaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this context was loaded"
    )
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make the model immutable
        json_schema_extra = {
            "example": {
                "user_id": "user-123",
                "fitness_level": "beginner",
                "primary_goal": "fat_loss",
                "secondary_goal": "general_fitness",
                "energy_level": "medium",
                "current_workout_plan": {
                    "plan_id": "workout-456",
                    "exercises": []
                },
                "current_meal_plan": {
                    "plan_id": "meal-789",
                    "meals": []
                },
                "conversation_history": [
                    {"role": "user", "content": "What should I eat today?"},
                    {"role": "assistant", "content": "Based on your meal plan..."}
                ],
                "loaded_at": "2026-02-04T12:00:00Z"
            }
        }


class AgentResponse(BaseModel):
    """
    Standardized response format from all agents.
    
    This model ensures consistent output structure across all specialized agents,
    making it easier to track agent behavior and debug interactions.
    
    Attributes:
        content: The agent's response text
        agent_type: Identifier for which agent handled this query
        tools_used: List of tools/functions called during processing
        metadata: Additional metadata about the response
    """
    
    content: str = Field(
        ...,
        description="The agent's response text"
    )
    
    agent_type: str = Field(
        ...,
        description="Identifier for which agent handled this query (e.g., 'test', 'workout', 'diet')"
    )
    
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools/functions called during processing"
    )
    
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional metadata about the response (e.g., mode, timestamp, tokens)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "content": "Based on your fitness level and goals, I recommend...",
                "agent_type": "workout",
                "tools_used": ["get_workout_plan", "calculate_calories"],
                "metadata": {
                    "mode": "text",
                    "timestamp": "2026-02-04T12:00:00Z",
                    "tokens_used": 150
                }
            }
        }
