"""
Demo script for TrackerAgent showing real-world usage scenarios.

This script demonstrates how the TrackerAgent would be used in practice
with various adherence levels and adjustment scenarios.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.tracker import TrackerAgent
from app.agents.context import AgentContext


async def demo_tracker_agent():
    """Demonstrate TrackerAgent capabilities."""
    
    print("=" * 80)
    print("TrackerAgent Demo - Real-World Usage Scenarios")
    print("=" * 80)
    
    # Create test context
    context = AgentContext(
        user_id="demo-user-456",
        fitness_level="intermediate",
        primary_goal="fat_loss",
        energy_level="medium",
        conversation_history=[]
    )
    
    # Instantiate agent
    agent = TrackerAgent(context=context, db_session=None)
    tools = agent.get_tools()
    
    print("\n" + "=" * 80)
    print("Scenario 1: Low Adherence - User Struggling with Consistency")
    print("=" * 80)
    
    adjustment_tool = tools[2]
    result = await adjustment_tool.ainvoke({
        "adherence_percentage": 35.0,
        "reason": "work stress and time constraints"
    })
    
    data = json.loads(result)
    if data["success"]:
        print(f"\nAdherence: {data['data']['adherence_percentage']}%")
        print(f"Adjustment Type: {data['data']['adjustment_type']}")
        print(f"\nSupportive Message:")
        print(f"  {data['data']['supportive_message']}")
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(data['data']['suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("Scenario 2: Good Adherence - User Maintaining Consistency")
    print("=" * 80)
    
    result = await adjustment_tool.ainvoke({
        "adherence_percentage": 78.0,
        "reason": "maintaining current routine"
    })
    
    data = json.loads(result)
    if data["success"]:
        print(f"\nAdherence: {data['data']['adherence_percentage']}%")
        print(f"Adjustment Type: {data['data']['adjustment_type']}")
        print(f"\nSupportive Message:")
        print(f"  {data['data']['supportive_message']}")
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(data['data']['suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("Scenario 3: Excellent Adherence - User Ready for Progression")
    print("=" * 80)
    
    result = await adjustment_tool.ainvoke({
        "adherence_percentage": 95.0,
        "reason": "feeling strong and consistent"
    })
    
    data = json.loads(result)
    if data["success"]:
        print(f"\nAdherence: {data['data']['adherence_percentage']}%")
        print(f"Adjustment Type: {data['data']['adjustment_type']}")
        print(f"\nSupportive Message:")
        print(f"  {data['data']['supportive_message']}")
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(data['data']['suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("Scenario 4: Moderate Adherence with Motivation Issues")
    print("=" * 80)
    
    result = await adjustment_tool.ainvoke({
        "adherence_percentage": 62.0,
        "reason": "losing motivation and feeling bored"
    })
    
    data = json.loads(result)
    if data["success"]:
        print(f"\nAdherence: {data['data']['adherence_percentage']}%")
        print(f"Adjustment Type: {data['data']['adjustment_type']}")
        print(f"\nSupportive Message:")
        print(f"  {data['data']['supportive_message']}")
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(data['data']['suggestions'], 1):
            print(f"  {i}. {suggestion}")
    
    print("\n" + "=" * 80)
    print("Scenario 5: Testing System Prompts")
    print("=" * 80)
    
    print("\nText Mode System Prompt (excerpt):")
    text_prompt = agent._system_prompt(voice_mode=False)
    print(text_prompt[:300] + "...")
    
    print("\n\nVoice Mode System Prompt (excerpt):")
    voice_prompt = agent._system_prompt(voice_mode=True)
    # Show the voice-specific instruction
    voice_instruction = voice_prompt.split("IMPORTANT:")[-1].strip()
    print(f"IMPORTANT: {voice_instruction}")
    
    print("\n" + "=" * 80)
    print("Scenario 6: Supportive Messages Across Adherence Spectrum")
    print("=" * 80)
    
    adherence_levels = [25, 45, 65, 80, 95]
    print("\nSupportive messages for different adherence levels:")
    for level in adherence_levels:
        message = agent._generate_supportive_message(float(level))
        print(f"\n{level}% adherence:")
        print(f"  {message}")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Agent provides context-aware suggestions based on adherence")
    print("  • Supportive, non-judgmental tone throughout")
    print("  • Adaptive recommendations (reduce/optimize/progress/maintain)")
    print("  • Considers user's specific reasons and context")
    print("  • Ready for integration with AgentOrchestrator")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_tracker_agent())
