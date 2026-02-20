"""Onboarding Agent Orchestrator Service.

This service orchestrates onboarding agents based on the user's current step.
It handles agent routing, context loading, and agent instantiation.
"""

from typing import Dict, List
from uuid import UUID
import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context import OnboardingAgentContext
from app.agents.onboarding.base import BaseOnboardingAgent
from app.agents.onboarding.diet_planning import DietPlanningAgent
from app.agents.onboarding.fitness_assessment import FitnessAssessmentAgent
from app.agents.onboarding.goal_setting import GoalSettingAgent
from app.agents.onboarding.scheduling import SchedulingAgent
from app.agents.onboarding.workout_planning import WorkoutPlanningAgent
from app.models.conversation import ConversationMessage
from app.models.onboarding import OnboardingState
from app.schemas.onboarding import OnboardingAgentType

logger = logging.getLogger(__name__)


class OnboardingAgentOrchestrator:
    """
    Orchestrates onboarding agents based on current step.
    
    Responsibilities:
    - Load onboarding state from database
    - Map current step to appropriate agent type
    - Instantiate agent with context
    - Route messages to the correct agent
    
    The orchestrator follows this step-to-agent mapping:
    - Steps 1-2: FITNESS_ASSESSMENT
    - Step 3: GOAL_SETTING
    - Steps 4-5: DIET_PLANNING
    - Steps 6-7: WORKOUT_PLANNING
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
        
        # Create and return agent (pass user_id for conversation history loading)
        return await self._create_agent(agent_type, context, user_id)
    
    def _step_to_agent(self, step: int) -> OnboardingAgentType:
        """
        Map onboarding step number to agent type.
        
        This method implements the step-to-agent routing logic:
        - Steps 1-2: Fitness Assessment (understanding current fitness level and goals)
        - Step 3: Goal Setting (workout constraints and equipment)
        - Steps 4-5: Diet Planning (dietary preferences and meal planning)
        - Steps 6-7: Workout Planning (meal and workout scheduling)
        - Steps 8-9: Scheduling (hydration and supplements)
        
        Args:
            step: Current onboarding step (1-9)
            
        Returns:
            OnboardingAgentType for this step
            
        Raises:
            ValueError: If step is out of valid range (1-9)
        """
        if step < 1 or step > 9:
            raise ValueError(f"Invalid onboarding step: {step}")
        
        if step <= 2:
            return OnboardingAgentType.FITNESS_ASSESSMENT
        elif step == 3:
            return OnboardingAgentType.GOAL_SETTING
        elif step <= 5:
            return OnboardingAgentType.DIET_PLANNING
        elif step <= 7:
            return OnboardingAgentType.WORKOUT_PLANNING
        else:  # steps 8-9
            return OnboardingAgentType.SCHEDULING
    
    async def _create_agent(
        self,
        agent_type: OnboardingAgentType,
        context_dict: dict,
        user_id: UUID
    ) -> BaseOnboardingAgent:
        """
        Factory method to create agent instance with conversation history.
        
        This method instantiates the appropriate agent class based on the
        agent type. It loads conversation history from the database and
        creates an OnboardingAgentContext with both the conversation history
        and the agent context from previous steps.
        
        Args:
            agent_type: Type of agent to create
            context_dict: Agent context from database (collected by previous agents)
            user_id: UUID of the user
            
        Returns:
            Instance of the appropriate agent class
            
        Raises:
            ValueError: If agent creation fails
        """
        try:
            # Load conversation history
            conversation_history = await self._load_conversation_history(user_id)
            
            # Create OnboardingAgentContext
            context = OnboardingAgentContext(
                user_id=str(user_id),
                conversation_history=conversation_history,
                agent_context=context_dict
            )
            
            # Instantiate agent
            agent_classes = {
                OnboardingAgentType.FITNESS_ASSESSMENT: FitnessAssessmentAgent,
                OnboardingAgentType.GOAL_SETTING: GoalSettingAgent,
                OnboardingAgentType.WORKOUT_PLANNING: WorkoutPlanningAgent,
                OnboardingAgentType.DIET_PLANNING: DietPlanningAgent,
                OnboardingAgentType.SCHEDULING: SchedulingAgent,
            }
            
            agent_class = agent_classes[agent_type]
            return agent_class(self.db, context)
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type} for {user_id}: {e}")
            raise ValueError(f"Agent creation failed: {e}")
    
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
    
    async def _load_conversation_history(self, user_id: UUID) -> List[Dict]:
        """
        Load recent conversation history for user.
        
        This method queries the ConversationMessage table to retrieve the user's
        recent conversation messages, ordered chronologically. The history is
        limited to the last 20 messages to prevent excessive token usage while
        maintaining sufficient context for natural conversations.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            List of messages in format [{"role": "user"|"assistant", "content": "..."}]
        """
        try:
            stmt = (
                select(ConversationMessage)
                .where(ConversationMessage.user_id == user_id)
                .order_by(ConversationMessage.created_at.asc())
                .limit(20)  # Limit to last 20 messages
            )
            
            result = await self.db.execute(stmt)
            messages = result.scalars().all()
            
            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Failed to load conversation history for {user_id}: {e}")
            return []  # Fallback to empty history
    
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
