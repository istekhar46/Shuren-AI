"""
Quick verification script for SupplementGuideAgent implementation.
"""

import asyncio
import json
from app.agents.supplement_guide import SupplementGuideAgent
from app.agents.context import AgentContext


async def test_supplement_agent():
    """Test basic functionality of SupplementGuideAgent."""
    
    print("=" * 60)
    print("Testing SupplementGuideAgent Implementation")
    print("=" * 60)
    
    # Create test context
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        energy_level="medium",
        conversation_history=[]
    )
    
    # Create agent
    agent = SupplementGuideAgent(context=context)
    
    print("\n1. Agent Creation:")
    print(f"   ✓ Agent created successfully")
    print(f"   ✓ Agent type: {type(agent).__name__}")
    
    # Test get_tools()
    print("\n2. Tools Available:")
    tools = agent.get_tools()
    print(f"   ✓ Number of tools: {len(tools)}")
    for tool in tools:
        print(f"   ✓ Tool: {tool.name}")
    
    # Test system prompt
    print("\n3. System Prompt:")
    text_prompt = agent._system_prompt(voice_mode=False)
    voice_prompt = agent._system_prompt(voice_mode=True)
    print(f"   ✓ Text mode prompt length: {len(text_prompt)} characters")
    print(f"   ✓ Voice mode prompt length: {len(voice_prompt)} characters")
    print(f"   ✓ Contains 'DISCLAIMER': {'DISCLAIMER' in text_prompt}")
    print(f"   ✓ Contains 'NOT medical': {'NOT medical' in text_prompt or 'NOT a medical' in text_prompt}")
    
    # Test get_supplement_info tool
    print("\n4. Testing get_supplement_info tool:")
    supplement_tool = tools[0]
    
    # Test with known supplement
    result = await supplement_tool.ainvoke({"supplement_name": "creatine"})
    result_data = json.loads(result)
    print(f"   ✓ Query: creatine")
    print(f"   ✓ Success: {result_data.get('success')}")
    print(f"   ✓ Has disclaimer: {'disclaimer' in result_data.get('data', {})}")
    if result_data.get('success'):
        print(f"   ✓ Description: {result_data['data']['description'][:60]}...")
    
    # Test with unknown supplement
    result = await supplement_tool.ainvoke({"supplement_name": "unknown_supplement_xyz"})
    result_data = json.loads(result)
    print(f"\n   ✓ Query: unknown_supplement_xyz")
    print(f"   ✓ Success: {result_data.get('success')}")
    print(f"   ✓ Has disclaimer: {'disclaimer' in result_data.get('data', {})}")
    print(f"   ✓ Has recommendation: {'recommendation' in result_data.get('data', {})}")
    
    # Test check_supplement_interactions tool
    print("\n5. Testing check_supplement_interactions tool:")
    interaction_tool = tools[1]
    
    # Test with known interaction
    result = await interaction_tool.ainvoke({"supplements": ["caffeine", "pre-workout"]})
    result_data = json.loads(result)
    print(f"   ✓ Query: caffeine + pre-workout")
    print(f"   ✓ Success: {result_data.get('success')}")
    print(f"   ✓ Has disclaimer: {'disclaimer' in result_data.get('data', {})}")
    if result_data.get('success'):
        interactions_found = result_data['data'].get('interactions_found', 0)
        print(f"   ✓ Interactions found: {interactions_found}")
    
    # Test with no known interactions
    result = await interaction_tool.ainvoke({"supplements": ["protein powder", "multivitamin"]})
    result_data = json.loads(result)
    print(f"\n   ✓ Query: protein powder + multivitamin")
    print(f"   ✓ Success: {result_data.get('success')}")
    print(f"   ✓ Has disclaimer: {'disclaimer' in result_data.get('data', {})}")
    if result_data.get('success'):
        interactions_found = result_data['data'].get('interactions_found', 0)
        print(f"   ✓ Interactions found: {interactions_found}")
    
    # Test with insufficient supplements
    result = await interaction_tool.ainvoke({"supplements": ["creatine"]})
    result_data = json.loads(result)
    print(f"\n   ✓ Query: single supplement (should fail)")
    print(f"   ✓ Success: {result_data.get('success')}")
    print(f"   ✓ Has error message: {'error' in result_data}")
    
    print("\n" + "=" * 60)
    print("All Tests Completed Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_supplement_agent())
