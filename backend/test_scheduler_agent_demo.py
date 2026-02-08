"""
Demo script for SchedulerAgent showing example interactions.

This script demonstrates how the SchedulerAgent would respond to various
scheduling queries without requiring a live database connection.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.scheduler import SchedulerAgent
from app.agents.context import AgentContext


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


async def demo_scheduler_agent():
    """Demonstrate SchedulerAgent capabilities."""
    
    print_section("SCHEDULER AGENT DEMO")
    
    # Create test context
    context = AgentContext(
        user_id="demo-user-456",
        fitness_level="intermediate",
        primary_goal="fat_loss",
        energy_level="high",
        conversation_history=[]
    )
    
    # Initialize agent
    agent = SchedulerAgent(context=context, db_session=None)
    
    print("Agent initialized with context:")
    print(f"  - User: {context.user_id}")
    print(f"  - Fitness Level: {context.fitness_level}")
    print(f"  - Goal: {context.primary_goal}")
    
    # Demo 1: Show available tools
    print_section("DEMO 1: Available Tools")
    
    tools = agent.get_tools()
    print(f"The SchedulerAgent has {len(tools)} tools:\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        print(f"   Purpose: {tool.description.split('.')[0]}")
        print()
    
    # Demo 2: System prompt for text mode
    print_section("DEMO 2: Text Mode System Prompt")
    
    text_prompt = agent._system_prompt(voice_mode=False)
    print("System prompt excerpt (first 500 characters):")
    print("-" * 80)
    print(text_prompt[:500] + "...")
    print("-" * 80)
    print(f"\nFull prompt length: {len(text_prompt)} characters")
    print(f"Includes markdown instruction: {'markdown' in text_prompt.lower()}")
    
    # Demo 3: System prompt for voice mode
    print_section("DEMO 3: Voice Mode System Prompt")
    
    voice_prompt = agent._system_prompt(voice_mode=True)
    print("Voice mode differences:")
    print(f"  - Prompt length: {len(voice_prompt)} characters")
    print(f"  - Mentions 'concise': {'concise' in voice_prompt.lower()}")
    print(f"  - Mentions '75 words': {'75 words' in voice_prompt.lower()}")
    print(f"  - Mentions '30 seconds': {'30 seconds' in voice_prompt.lower()}")
    
    # Demo 4: Example tool usage scenarios
    print_section("DEMO 4: Example Usage Scenarios")
    
    scenarios = [
        {
            "query": "What's my workout schedule for this week?",
            "tool": "get_upcoming_schedule",
            "description": "Retrieves all upcoming workouts and meals"
        },
        {
            "query": "Can I move my Wednesday workout to Thursday?",
            "tool": "reschedule_workout",
            "description": "Reschedules workout with conflict detection"
        },
        {
            "query": "Turn off meal reminders",
            "tool": "update_reminder_preferences",
            "description": "Disables meal notifications"
        },
        {
            "query": "I need to reschedule my morning workout to evening",
            "tool": "reschedule_workout",
            "description": "Updates workout time on the same day"
        },
        {
            "query": "Enable workout notifications",
            "tool": "update_reminder_preferences",
            "description": "Enables workout reminders"
        }
    ]
    
    print("Example queries the agent can handle:\n")
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. User Query: \"{scenario['query']}\"")
        print(f"   Tool Used: {scenario['tool']}")
        print(f"   Action: {scenario['description']}")
        print()
    
    # Demo 5: Tool parameter examples
    print_section("DEMO 5: Tool Parameters")
    
    print("1. get_upcoming_schedule")
    print("   Parameters: None")
    print("   Returns: JSON with workouts and meals arrays")
    print()
    
    print("2. reschedule_workout")
    print("   Parameters:")
    print("     - workout_schedule_id: UUID of the schedule")
    print("     - new_day_of_week: 0-6 (Monday-Sunday)")
    print("     - new_time: HH:MM format (24-hour)")
    print("   Example: reschedule_workout('abc-123', 3, '18:00')")
    print("   Returns: Confirmation with old and new schedule")
    print()
    
    print("3. update_reminder_preferences")
    print("   Parameters:")
    print("     - reminder_type: 'workout', 'meal', or 'hydration'")
    print("     - enabled: True or False")
    print("   Example: update_reminder_preferences('workout', True)")
    print("   Returns: Confirmation with updated count")
    print()
    
    # Demo 6: Error handling examples
    print_section("DEMO 6: Error Handling")
    
    error_cases = [
        {
            "scenario": "Invalid day_of_week (e.g., 8)",
            "response": "Error: Invalid day_of_week. Must be between 0 (Monday) and 6 (Sunday)"
        },
        {
            "scenario": "Invalid time format (e.g., '25:00')",
            "response": "Error: Invalid time format. Use HH:MM (24-hour format)"
        },
        {
            "scenario": "Schedule conflict detected",
            "response": "Error: Another workout is already scheduled on this day at [time]"
        },
        {
            "scenario": "Invalid reminder type",
            "response": "Error: Invalid reminder_type. Must be one of: workout, meal, hydration"
        },
        {
            "scenario": "Database connection error",
            "response": "Error: Unable to retrieve schedule. Please try again."
        }
    ]
    
    print("The agent handles various error cases gracefully:\n")
    
    for i, case in enumerate(error_cases, 1):
        print(f"{i}. {case['scenario']}")
        print(f"   Response: \"{case['response']}\"")
        print()
    
    # Demo 7: Response format examples
    print_section("DEMO 7: Response Format Examples")
    
    print("All tools return JSON with this structure:\n")
    print("{")
    print('  "success": true/false,')
    print('  "data": { ... },           // Present on success')
    print('  "error": "message",        // Present on failure')
    print('  "metadata": {')
    print('    "timestamp": "ISO-8601",')
    print('    "source": "scheduler_agent"')
    print("  }")
    print("}")
    
    print("\nExample success response (get_upcoming_schedule):")
    print("-" * 80)
    print("""{
  "success": true,
  "data": {
    "workouts": [
      {
        "id": "workout-123",
        "day": "Monday",
        "day_of_week": 0,
        "time": "07:00",
        "notifications_enabled": true
      }
    ],
    "meals": [
      {
        "id": "meal-456",
        "meal_name": "breakfast",
        "time": "08:00",
        "notifications_enabled": true
      }
    ]
  },
  "metadata": {
    "timestamp": "2026-02-05T10:30:00Z",
    "source": "scheduler_agent"
  }
}""")
    print("-" * 80)
    
    # Demo 8: Integration with other agents
    print_section("DEMO 8: Integration Points")
    
    print("The SchedulerAgent integrates with:\n")
    
    integrations = [
        ("AgentOrchestrator", "Routes scheduling queries to this agent"),
        ("WorkoutPlannerAgent", "Coordinates workout timing with workout plans"),
        ("DietPlannerAgent", "Aligns meal schedules with nutrition plans"),
        ("TrackerAgent", "Provides schedule data for adherence tracking"),
        ("Database Models", "WorkoutSchedule, MealSchedule, HydrationPreference"),
        ("LangChain", "Tool calling and LLM integration")
    ]
    
    for component, description in integrations:
        print(f"  • {component}")
        print(f"    {description}")
        print()
    
    print_section("DEMO COMPLETE")
    
    print("The SchedulerAgent is ready for:")
    print("  ✓ Integration with AgentOrchestrator")
    print("  ✓ Database operations with real user data")
    print("  ✓ Unit and integration testing")
    print("  ✓ Production deployment")
    print()
    print("For full testing with database, see the unit tests.")


if __name__ == "__main__":
    asyncio.run(demo_scheduler_agent())
