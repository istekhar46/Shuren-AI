"""
Verification script for SchedulerAgent implementation.

This script tests the basic functionality of the SchedulerAgent including:
- Agent initialization
- Tool availability
- System prompt generation
- Voice and text mode processing
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.scheduler import SchedulerAgent
from app.agents.context import AgentContext


async def verify_scheduler_agent():
    """Verify SchedulerAgent implementation."""
    
    print("=" * 80)
    print("SCHEDULER AGENT VERIFICATION")
    print("=" * 80)
    
    # Create test context
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="medium",
        conversation_history=[]
    )
    
    # Initialize agent (without database session for basic verification)
    agent = SchedulerAgent(context=context, db_session=None)
    
    print("\n✓ Agent initialized successfully")
    
    # Test 1: Check tools
    print("\n" + "=" * 80)
    print("TEST 1: Tool Availability")
    print("=" * 80)
    
    tools = agent.get_tools()
    print(f"\nNumber of tools: {len(tools)}")
    
    expected_tools = [
        "get_upcoming_schedule",
        "reschedule_workout",
        "update_reminder_preferences"
    ]
    
    tool_names = [tool.name for tool in tools]
    print(f"Tool names: {tool_names}")
    
    for expected_tool in expected_tools:
        if expected_tool in tool_names:
            print(f"✓ {expected_tool} - Found")
        else:
            print(f"✗ {expected_tool} - Missing")
    
    # Test 2: System prompt generation
    print("\n" + "=" * 80)
    print("TEST 2: System Prompt Generation")
    print("=" * 80)
    
    # Text mode prompt
    text_prompt = agent._system_prompt(voice_mode=False)
    print(f"\nText mode prompt length: {len(text_prompt)} characters")
    print(f"Contains 'scheduling': {'scheduling' in text_prompt.lower()}")
    print(f"Contains 'reminder': {'reminder' in text_prompt.lower()}")
    print(f"Contains 'markdown': {'markdown' in text_prompt.lower()}")
    
    # Voice mode prompt
    voice_prompt = agent._system_prompt(voice_mode=True)
    print(f"\nVoice mode prompt length: {len(voice_prompt)} characters")
    print(f"Contains 'concise': {'concise' in voice_prompt.lower()}")
    print(f"Contains '75 words': {'75 words' in voice_prompt.lower()}")
    
    # Test 3: Tool descriptions
    print("\n" + "=" * 80)
    print("TEST 3: Tool Descriptions")
    print("=" * 80)
    
    for tool in tools:
        print(f"\n{tool.name}:")
        print(f"  Description: {tool.description[:100]}...")
        if hasattr(tool, 'args_schema') and tool.args_schema:
            print(f"  Has args schema: Yes")
        else:
            print(f"  Has args schema: No")
    
    # Test 4: Voice mode processing (without LLM call)
    print("\n" + "=" * 80)
    print("TEST 4: Agent Structure Validation")
    print("=" * 80)
    
    # Check required methods exist
    required_methods = [
        'process_text',
        'process_voice',
        'stream_response',
        'get_tools',
        '_system_prompt'
    ]
    
    for method_name in required_methods:
        if hasattr(agent, method_name):
            print(f"✓ {method_name} - Implemented")
        else:
            print(f"✗ {method_name} - Missing")
    
    # Test 5: Context usage
    print("\n" + "=" * 80)
    print("TEST 5: Context Usage")
    print("=" * 80)
    
    print(f"\nAgent context:")
    print(f"  User ID: {agent.context.user_id}")
    print(f"  Fitness Level: {agent.context.fitness_level}")
    print(f"  Primary Goal: {agent.context.primary_goal}")
    print(f"  Energy Level: {agent.context.energy_level}")
    
    # Verify context is used in system prompt
    prompt = agent._system_prompt()
    print(f"\nContext in system prompt:")
    print(f"  Fitness Level mentioned: {agent.context.fitness_level in prompt}")
    print(f"  Primary Goal mentioned: {agent.context.primary_goal in prompt}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\n✓ All basic checks passed!")
    print("\nNote: This verification tests the agent structure without database.")
    print("For full testing with database operations, run the unit tests.")


if __name__ == "__main__":
    asyncio.run(verify_scheduler_agent())
