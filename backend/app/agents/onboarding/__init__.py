"""Onboarding agents package."""

from app.agents.onboarding.base import BaseOnboardingAgent
from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.agents.onboarding.scheduling import SchedulingAgent
from app.agents.onboarding.workout_planning import WorkoutPlanningAgent

__all__ = [
    "BaseOnboardingAgent",
    "DietPlanningAgent",
    "FitnessAssessmentAgent",
    "GoalSettingAgent",
    "SchedulingAgent",
    "WorkoutPlanningAgent",
]
