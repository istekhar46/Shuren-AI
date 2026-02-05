"""
Verification script for TrackerAgent implementation.

This script tests the basic functionality of the TrackerAgent to ensure
all methods are implemented correctly and the agent can be instantiated.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.tracker import TrackerAgent
from app.agents.context import AgentContext


async def verify_tracker_agent():
    """Verify TrackerAgent implementation."""
    
    print("=" * 80)
    print("TrackerAgent Verification")
    print("=" * 80)
    
    # Create test context
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="medium",
        conversation_history=[]
    )
    
    print("\n1. Testing TrackerAgent instantiation...")
    try:
        agent = TrackerAgent(context=context, db_session=None)
        print("   ✓ TrackerAgent instantiated successfully")
    except Exception as e:
        print(f"   ✗ Failed to instantiate TrackerAgent: {e}")
        return False
    
    print("\n2. Testing get_tools() method...")
    try:
        tools = agent.get_tools()
        print(f"   ✓ get_tools() returned {len(tools)} tools")
        
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_workout_adherence",
            "get_progress_metrics",
            "suggest_plan_adjustment"
        ]
        
        for expected_tool in expected_tools:
            if expected_tool in tool_names:
                print(f"   ✓ Tool '{expected_tool}' found")
            else:
                print(f"   ✗ Tool '{expected_tool}' missing")
                return False
                
    except Exception as e:
        print(f"   ✗ Failed to get tools: {e}")
        return False
    
    print("\n3. Testing _system_prompt() method...")
    try:
        # Test text mode prompt
        text_prompt = agent._system_prompt(voice_mode=False)
        if "progress tracking" in text_prompt.lower():
            print("   ✓ Text mode system prompt generated")
        else:
            print("   ✗ Text mode system prompt missing key content")
            return False
        
        # Test voice mode prompt
        voice_prompt = agent._system_prompt(voice_mode=True)
        if "concise" in voice_prompt.lower():
            print("   ✓ Voice mode system prompt generated")
        else:
            print("   ✗ Voice mode system prompt missing voice instructions")
            return False
            
    except Exception as e:
        print(f"   ✗ Failed to generate system prompt: {e}")
        return False
    
    print("\n4. Testing tool execution (without database)...")
    try:
        import json
        
        # Test get_workout_adherence tool
        adherence_tool = tools[0]
        result = await adherence_tool.ainvoke({"days": 30})
        result_data = json.loads(result)
        
        # Without database, we expect either success with note or error about database
        if result_data.get("success") is False and "Database session not available" in result_data.get("error", ""):
            print("   ✓ get_workout_adherence tool handles missing database correctly")
        elif result_data.get("success") and "note" in result_data.get("data", {}):
            print("   ✓ get_workout_adherence tool executed")
        else:
            print(f"   ✗ get_workout_adherence tool unexpected response: {result_data}")
            return False
        
        # Test get_progress_metrics tool
        metrics_tool = tools[1]
        result = await metrics_tool.ainvoke({})
        result_data = json.loads(result)
        
        if result_data.get("success") is False and "Database session not available" in result_data.get("error", ""):
            print("   ✓ get_progress_metrics tool handles missing database correctly")
        elif result_data.get("success") and "note" in result_data.get("data", {}):
            print("   ✓ get_progress_metrics tool executed")
        else:
            print(f"   ✗ get_progress_metrics tool unexpected response: {result_data}")
            return False
        
        # Test suggest_plan_adjustment tool (doesn't require database)
        adjustment_tool = tools[2]
        result = await adjustment_tool.ainvoke({
            "adherence_percentage": 65.0,
            "reason": "time constraints"
        })
        result_data = json.loads(result)
        
        if result_data.get("success"):
            print("   ✓ suggest_plan_adjustment tool executed")
            
            # Verify suggestions are present
            suggestions = result_data.get("data", {}).get("suggestions", [])
            if len(suggestions) > 0:
                print(f"   ✓ Generated {len(suggestions)} adjustment suggestions")
            else:
                print("   ✗ No suggestions generated")
                return False
        else:
            print(f"   ✗ suggest_plan_adjustment tool failed: {result_data}")
            return False
            
    except Exception as e:
        print(f"   ✗ Failed to execute tools: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n5. Testing _generate_supportive_message() helper...")
    try:
        # Test different adherence levels
        low_message = agent._generate_supportive_message(40.0)
        medium_message = agent._generate_supportive_message(75.0)
        high_message = agent._generate_supportive_message(95.0)
        
        if all([low_message, medium_message, high_message]):
            print("   ✓ Supportive messages generated for all adherence levels")
            print(f"      Low adherence: {low_message[:50]}...")
            print(f"      Medium adherence: {medium_message[:50]}...")
            print(f"      High adherence: {high_message[:50]}...")
        else:
            print("   ✗ Failed to generate supportive messages")
            return False
            
    except Exception as e:
        print(f"   ✗ Failed to generate supportive messages: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✓ All TrackerAgent verification tests passed!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_tracker_agent())
    sys.exit(0 if success else 1)
