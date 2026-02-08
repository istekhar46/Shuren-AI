"""
Quick verification script to check all agents work independently.

This script verifies:
1. All 6 specialized agents can be instantiated
2. Each agent has the required methods
3. Each agent has the correct tools
"""

from app.agents.context import AgentContext
from app.agents.workout_planner import WorkoutPlannerAgent
from app.agents.diet_planner import DietPlannerAgent
from app.agents.supplement_guide import SupplementGuideAgent
from app.agents.tracker import TrackerAgent
from app.agents.scheduler import SchedulerAgent
from app.agents.general_assistant import GeneralAssistantAgent


def verify_agent(agent_class, agent_name, expected_tool_count):
    """Verify an agent has all required methods and tools."""
    print(f"\n{'='*60}")
    print(f"Verifying {agent_name}...")
    print(f"{'='*60}")
    
    # Create test context
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="fat_loss",
        energy_level="medium"
    )
    
    # Instantiate agent
    try:
        agent = agent_class(context=context)
        print(f"✓ {agent_name} instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate {agent_name}: {e}")
        return False
    
    # Check required methods
    required_methods = [
        'process_text',
        'process_voice',
        'stream_response',
        'get_tools',
        '_system_prompt'
    ]
    
    for method in required_methods:
        if hasattr(agent, method):
            print(f"✓ Has method: {method}")
        else:
            print(f"✗ Missing method: {method}")
            return False
    
    # Check tools
    try:
        tools = agent.get_tools()
        print(f"✓ Has {len(tools)} tools (expected {expected_tool_count})")
        
        if len(tools) != expected_tool_count:
            print(f"✗ Tool count mismatch: expected {expected_tool_count}, got {len(tools)}")
            return False
        
        # Print tool names
        for tool in tools:
            print(f"  - {tool.name}")
    except Exception as e:
        print(f"✗ Failed to get tools: {e}")
        return False
    
    # Check system prompt generation
    try:
        text_prompt = agent._system_prompt(voice_mode=False)
        voice_prompt = agent._system_prompt(voice_mode=True)
        print(f"✓ System prompts generated successfully")
        print(f"  - Text prompt length: {len(text_prompt)} chars")
        print(f"  - Voice prompt length: {len(voice_prompt)} chars")
    except Exception as e:
        print(f"✗ Failed to generate system prompts: {e}")
        return False
    
    print(f"\n✓ {agent_name} verification PASSED")
    return True


def main():
    """Run verification for all agents."""
    print("\n" + "="*60)
    print("AGENT VERIFICATION SCRIPT")
    print("="*60)
    
    agents_to_verify = [
        (WorkoutPlannerAgent, "WorkoutPlannerAgent", 4),
        (DietPlannerAgent, "DietPlannerAgent", 4),
        (SupplementGuideAgent, "SupplementGuideAgent", 2),
        (TrackerAgent, "TrackerAgent", 3),
        (SchedulerAgent, "SchedulerAgent", 3),
        (GeneralAssistantAgent, "GeneralAssistantAgent", 2),
    ]
    
    results = []
    for agent_class, agent_name, tool_count in agents_to_verify:
        success = verify_agent(agent_class, agent_name, tool_count)
        results.append((agent_name, success))
    
    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    for agent_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {agent_name}")
    
    all_passed = all(success for _, success in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL AGENTS VERIFIED SUCCESSFULLY")
    else:
        print("✗ SOME AGENTS FAILED VERIFICATION")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
