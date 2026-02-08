"""
Quick demo script to verify GeneralAssistantAgent functionality.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.agents.general_assistant import GeneralAssistantAgent
from app.agents.context import AgentContext


async def test_general_assistant():
    """Test GeneralAssistantAgent basic functionality."""
    
    print("=" * 80)
    print("GENERAL ASSISTANT AGENT DEMO")
    print("=" * 80)
    
    # Create test context
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="high"
    )
    
    # Create agent (without database for basic testing)
    agent = GeneralAssistantAgent(context=context, db_session=None)
    
    print("\n1. Testing System Prompt Generation")
    print("-" * 80)
    
    # Test text mode prompt
    text_prompt = agent._system_prompt(voice_mode=False)
    print("Text Mode Prompt Length:", len(text_prompt))
    assert "friendly fitness assistant" in text_prompt.lower()
    assert "markdown" in text_prompt.lower()
    assert context.fitness_level in text_prompt
    assert context.primary_goal in text_prompt
    print("✓ Text mode prompt generated correctly")
    
    # Test voice mode prompt
    voice_prompt = agent._system_prompt(voice_mode=True)
    print("Voice Mode Prompt Length:", len(voice_prompt))
    assert "friendly fitness assistant" in voice_prompt.lower()
    assert "concise" in voice_prompt.lower() or "75 words" in voice_prompt.lower()
    assert context.fitness_level in voice_prompt
    print("✓ Voice mode prompt generated correctly")
    
    print("\n2. Testing Tool Availability")
    print("-" * 80)
    
    tools = agent.get_tools()
    print(f"Number of tools: {len(tools)}")
    
    tool_names = [tool.name for tool in tools]
    print(f"Tool names: {tool_names}")
    
    assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"
    assert "get_user_stats" in tool_names
    assert "provide_motivation" in tool_names
    print("✓ All required tools are available")
    
    print("\n3. Testing Tool Schemas")
    print("-" * 80)
    
    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        
        if tool.name == "get_user_stats":
            assert "statistics" in tool.description.lower() or "stats" in tool.description.lower()
            print("✓ get_user_stats has proper description")
        
        elif tool.name == "provide_motivation":
            assert "motivation" in tool.description.lower()
            print("✓ provide_motivation has proper description")
    
    print("\n4. Testing provide_motivation Tool (No DB Required)")
    print("-" * 80)
    
    # Test provide_motivation which doesn't need database
    motivation_tool = next(t for t in tools if t.name == "provide_motivation")
    
    try:
        result = await motivation_tool.ainvoke({})
        print(f"Motivation result: {result[:200]}...")
        
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "data" in data
        assert "messages" in data["data"]
        assert len(data["data"]["messages"]) > 0
        print(f"✓ provide_motivation returned {len(data['data']['messages'])} motivational messages")
        
        # Check context is included
        assert "context" in data["data"]
        assert data["data"]["context"]["fitness_level"] == context.fitness_level
        assert data["data"]["context"]["primary_goal"] == context.primary_goal
        print("✓ Motivation includes user context")
        
    except Exception as e:
        print(f"✗ Error testing provide_motivation: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE - ALL CHECKS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("✓ System prompts generated correctly for both modes")
    print("✓ All 2 required tools are available")
    print("✓ Tool descriptions are appropriate")
    print("✓ provide_motivation tool works without database")
    print("\nNote: get_user_stats requires database connection and will be tested in integration tests")


if __name__ == "__main__":
    asyncio.run(test_general_assistant())
