"""Onboarding Agent Orchestrator Service.

This service orchestrates onboarding agents based on the user's current step.
It handles agent routing, context loading, and agent instantiation.
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.onboarding.base import BaseOnboardingAgent
from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.agents.onboarding.scheduling import SchedulingAgent
from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import OnboardingAgentType


class OnboardingAgentOrchestrator:
    """
    Orchestrates onboarding agents based on current step.
    
    Responsibilities:
    - Load onboarding state from database
    - Map current step to appropriate agent type
    - Instantiate agent with context
    - Route messages to the correct agent
    
    The orchestrator follows this step-to-agent mapping:
    - Steps 0-2: FITNESS_ASSESSMENT
    - Step 3: GOAL_SETTING
    - Steps 4-5: WORKOUT_PLANNING
    - Steps 6-7: DIET_PLANNING
    - Steps 8-9: SCHEDULING
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize orchestrator with database session.
        
        Args:
            db: Async database session for database operations
        """
        self.db = db
    
    async def get_current_agent(
        self,
        user_id: UUID
    ) -> BaseOnboardingAgent:
        """
        Get the appropriate agent for user's current onboarding step.
        
        This method loads the user's onboarding state, determines which agent
        should handle their current step, and instantiates that agent with
        the appropriate context from previous steps.
        
        If onboarding is complete, this method raises ValueError to indicate
        that onboarding agents should not be used. The caller should route
        to the general assistant instead.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Instance of the appropriate onboarding agent
            
        Raises:
            ValueError: If step is invalid, user not found, or onboarding is complete
        """
        # Load onboarding state
        state = await self._load_onboarding_state(user_id)
        
        if not state:
            raise ValueError(f"No onboarding state found for user {user_id}")
        
        # Check if onboarding is complete
        if state.is_complete:
            raise ValueError(
                f"Onboarding already complete for user {user_id}. "
                "Route to general assistant instead."
            )
        
        # Determine agent type from step
        agent_type = self._step_to_agent(state.current_step)
        
        # Load context
        context = state.agent_context or {}
        
        # Create and return agent
        return await self._create_agent(agent_type, context)
    
    def _step_to_agent(self, step: int) -> OnboardingAgentType:
        """
        Map onboarding step number to agent type.
        
        This method implements the step-to-agent routing logic:
        - Steps 0-2: Fitness Assessment (understanding current fitness level)
        - Step 3: Goal Setting (defining fitness objectives)
        - Steps 4-5: Workout Planning (creating workout plans)
        - Steps 6-7: Diet Planning (building meal plans)
        - Steps 8-9: Scheduling (setting up daily schedule)
        
        Args:
            step: Current onboarding step (0-9)
            
        Returns:
            OnboardingAgentType for this step
            
        Raises:
            ValueError: If step is out of valid range (0-9)
        """
        if step < 0 or step > 9:
            raise ValueError(f"Invalid onboarding step: {step}")
        
        if step <= 2:
            return OnboardingAgentType.FITNESS_ASSESSMENT
        elif step == 3:
            return OnboardingAgentType.GOAL_SETTING
        elif step <= 5:
            return OnboardingAgentType.WORKOUT_PLANNING
        elif step <= 7:
            return OnboardingAgentType.DIET_PLANNING
        else:  # steps 8-9
            return OnboardingAgentType.SCHEDULING
    
    async def _create_agent(
        self,
        agent_type: OnboardingAgentType,
        context: dict
    ) -> BaseOnboardingAgent:
        """
        Factory method to create agent instance.
        
        This method instantiates the appropriate agent class based on the
        agent type, passing the database session and context from previous
        agents to enable context continuity.
        
        Args:
            agent_type: Type of agent to create
            context: Agent context from database (collected by previous agents)
            
        Returns:
            Instance of the appropriate agent class
        """
        agent_classes = {
            OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
            OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
            OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
            OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
            OnboardingAgentType.SCHEDULING: SchedulingAgent,
        }
        
        agent_class = agent_classes[agent_type]
        return agent_class(self.db, context)
    
    async def _load_onboarding_state(
        self,
        user_id: UUID
    ) -> OnboardingState | None:
        """
        Load onboarding state from database.
        
        This method queries the database for the user's onboarding state,
        which contains their current step, agent context, and conversation
        history.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            OnboardingState or None if not found
        """
        stmt = select(OnboardingState).where(
            OnboardingState.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def advance_step(
        self,
        user_id: UUID
    ) -> None:
        """
        Advance user to the next onboarding step.
        
        This method is called when an agent completes its work (step_complete=True).
        It increments the current_step and updates current_agent to reflect the
        new agent type that will handle the next step.
        
        Args:
            user_id: UUID of the user
            
        Raises:
            ValueError: If no onboarding state exists for user
        """
        # Load current state
        state = await self._load_onboarding_state(user_id)
        
        if not state:
            raise ValueError(f"No onboarding state found for user {user_id}")
        
        # Increment step
        new_step = state.current_step + 1
        
        # Determine new agent type
        new_agent_type = self._step_to_agent(new_step)
        
        # Update database
        stmt = (
            update(OnboardingState)
            .where(OnboardingState.user_id == user_id)
            .values(
                current_step=new_step,
                current_agent=new_agent_type.value
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
