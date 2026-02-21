"""
Test agent implementation for validating the base agent framework.

This module provides a simple test agent that extends BaseAgent to verify
the framework functionality before building specialized agents. It implements
all required abstract methods with minimal logic.
"""

from typing import AsyncIterator, List

from app.agents.base import BaseAgent
from app.agents.context import AgentResponse


class TestAgent(BaseAgent):
    """
    Simple test agent for validating the base agent framework.
    
    This agent provides minimal implementations of all required abstract methods
    to verify that the BaseAgent framework works correctly. It does not include
    complex logic or domain-specific tools - its purpose is purely for testing
    the infrastructure.
    
    The TestAgent:
    - Responds to text queries with detailed AgentResponse
    - Responds to voice queries with concise strings
    - Supports streaming responses
    - Has no tools (returns empty list)
    - Uses a basic system prompt for testing
    """
    
    async def process_text(self, query: str) -> AgentResponse:
        """
        Process a text query and return a detailed response.
        
        Builds messages with full conversation history (voice_mode=False),
        calls the LLM, and returns a structured AgentResponse.
        
        Args:
            query: User's text query
            
        Returns:
            AgentResponse with content, agent type, and metadata
        """
        # Build messages with full history for text mode
        messages = self._build_messages(query, voice_mode=False)
        
        # Call LLM
        response = await self.llm.ainvoke(messages)
        
        # Return structured response
        return AgentResponse(
            content=response.content,
            agent_type="test",
            tools_used=[],
            metadata={
                "mode": "text",
                "user_id": self.context.user_id,
                "fitness_level": self.context.fitness_level
            }
        )
    
    async def process_voice(self, query: str) -> str:
        """
        Process a voice query and return a concise response.
        
        Builds messages with limited conversation history (voice_mode=True),
        calls the LLM, and returns a plain string suitable for text-to-speech.
        
        Args:
            query: User's voice query (transcribed to text)
            
        Returns:
            str: Concise response text suitable for text-to-speech
        """
        # Build messages with limited history for voice mode
        messages = self._build_messages(query, voice_mode=True)
        
        # Call LLM
        response = await self.llm.ainvoke(messages)
        
        # Return plain string for voice
        return response.content
    
    async def stream_response(self, query: str) -> AsyncIterator[str]:
        """
        Stream response chunks for real-time display.
        
        Builds messages and uses the LLM's streaming capability to yield
        response chunks as they are generated.
        
        Args:
            query: User's query
            
        Yields:
            str: Response chunks as they are generated
        """
        # Build messages
        messages = self._build_messages(query, voice_mode=False)
        
        # Stream response chunks
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    
    def get_tools(self) -> List:
        """
        Get the list of tools available to this agent.
        
        The test agent has no tools - it's purely for validating the framework.
        
        Returns:
            List: Empty list (no tools for test agent)
        """
        return []
    
    def _system_prompt(self, voice_mode: bool = False) -> str:
        """
        Generate the system prompt for the test agent.
        
        Creates a basic system prompt that includes user context and
        appropriate instructions based on the interaction mode.
        
        Args:
            voice_mode: Whether this is a voice interaction
            
        Returns:
            str: System prompt for the LLM
        """
        base_prompt = f"""You are a test AI assistant for the Shuren fitness coaching system.

User Context:
- Fitness Level: {self.context.fitness_level}
- Primary Goal: {self.context.primary_goal}
- Energy Level: {self.context.energy_level}

This is a test agent used to validate the agent framework. Respond helpfully
to user queries while acknowledging that you are a test agent."""
        
        if voice_mode:
            base_prompt += "\n\nIMPORTANT: Keep responses concise and conversational for voice interaction."
        
        return base_prompt
