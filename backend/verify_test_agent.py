"""
Verification script for TestAgent implementation.

This script tests the TestAgent to ensure it works correctly:
1. Test import
2. Create TestAgent instance
3. Test text response
4. Test voice response
"""

import asyncio
from datetime import datetime

# Test 1: Import TestAgent
print("=" * 60)
print("Test 1: Import TestAgent")
print("=" * 60)
try:
    from app.agents.test_agent import TestAgent
    print("✓ Successfully imported TestAgent")
except Exception as e:
    print(f"✗ Failed to import TestAgent: {e}")
    exit(1)

# Import dependencies for testing
from app.agents.context import AgentContext


async def main():
    """Run verification tests."""
    
    # Test 2: Create TestAgent instance
    print("\n" + "=" * 60)
    print("Test 2: Create TestAgent instance")
    print("=" * 60)
    
    try:
        # Create a test context
        context = AgentContext(
            user_id="test-user-123",
            fitness_level="beginner",
            primary_goal="fat_loss",
            secondary_goal="general_fitness",
            energy_level="medium",
            current_workout_plan={"plan_id": "test-workout"},
            current_meal_plan={"plan_id": "test-meal"},
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you today?"}
            ],
            loaded_at=datetime.utcnow()
        )
        print(f"✓ Created AgentContext: user_id={context.user_id}, fitness_level={context.fitness_level}")
        
        # Create TestAgent instance
        agent = TestAgent(context=context, db_session=None)
        print(f"✓ Created TestAgent instance")
        print(f"  - Agent has LLM: {agent.llm is not None}")
        print(f"  - Agent has context: {agent.context is not None}")
        print(f"  - Context is immutable: {agent.context.__config__.frozen}")
        
    except Exception as e:
        print(f"✗ Failed to create TestAgent: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Test 3: Test text response
    print("\n" + "=" * 60)
    print("Test 3: Test text response")
    print("=" * 60)
    
    try:
        query = "What is my fitness level?"
        print(f"Query: {query}")
        
        response = await agent.process_text(query)
        
        print(f"✓ Received text response")
        print(f"  - Response type: {type(response).__name__}")
        print(f"  - Agent type: {response.agent_type}")
        print(f"  - Content length: {len(response.content)} characters")
        print(f"  - Tools used: {response.tools_used}")
        print(f"  - Metadata: {response.metadata}")
        print(f"\n  Response content (first 200 chars):")
        print(f"  {response.content[:200]}...")
        
        # Verify response structure
        assert response.agent_type == "test", "Agent type should be 'test'"
        assert len(response.content) > 0, "Response content should not be empty"
        assert isinstance(response.tools_used, list), "Tools used should be a list"
        assert isinstance(response.metadata, dict), "Metadata should be a dict"
        print("\n✓ Text response validation passed")
        
    except Exception as e:
        print(f"✗ Failed text response test: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Test 4: Test voice response
    print("\n" + "=" * 60)
    print("Test 4: Test voice response")
    print("=" * 60)
    
    try:
        query = "What should I focus on today?"
        print(f"Query: {query}")
        
        response = await agent.process_voice(query)
        
        print(f"✓ Received voice response")
        print(f"  - Response type: {type(response).__name__}")
        print(f"  - Content length: {len(response)} characters")
        print(f"\n  Response content:")
        print(f"  {response}")
        
        # Verify response structure
        assert isinstance(response, str), "Voice response should be a string"
        assert len(response) > 0, "Voice response should not be empty"
        print("\n✓ Voice response validation passed")
        
    except Exception as e:
        print(f"✗ Failed voice response test: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print("✓ All tests passed successfully!")
    print("\nTestAgent verification complete:")
    print("  1. ✓ Import successful")
    print("  2. ✓ Instance creation successful")
    print("  3. ✓ Text response working")
    print("  4. ✓ Voice response working")
    print("\nThe TestAgent is ready for use!")


if __name__ == "__main__":
    asyncio.run(main())
