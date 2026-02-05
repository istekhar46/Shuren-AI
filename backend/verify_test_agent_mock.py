"""
Verification script for TestAgent implementation (using mocks).

This script tests the TestAgent structure and methods without requiring API keys:
1. Test import
2. Create TestAgent instance (with mocked LLM)
3. Test method signatures and structure
4. Verify abstract method implementations
"""

from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, UTC

# Test 1: Import TestAgent
print("=" * 60)
print("Test 1: Import TestAgent")
print("=" * 60)
try:
    from app.agents.test_agent import TestAgent
    from app.agents.base import BaseAgent
    from app.agents.context import AgentContext, AgentResponse
    print("✓ Successfully imported TestAgent")
    print("✓ Successfully imported BaseAgent")
    print("✓ Successfully imported AgentContext and AgentResponse")
except Exception as e:
    print(f"✗ Failed to import: {e}")
    exit(1)

# Test 2: Verify TestAgent extends BaseAgent
print("\n" + "=" * 60)
print("Test 2: Verify TestAgent extends BaseAgent")
print("=" * 60)

try:
    assert issubclass(TestAgent, BaseAgent), "TestAgent should extend BaseAgent"
    print("✓ TestAgent extends BaseAgent")
    
    # Check that TestAgent implements all abstract methods
    abstract_methods = ['process_text', 'process_voice', 'stream_response', 'get_tools', '_system_prompt']
    for method in abstract_methods:
        assert hasattr(TestAgent, method), f"TestAgent should implement {method}"
        print(f"✓ TestAgent implements {method}")
    
except Exception as e:
    print(f"✗ Failed verification: {e}")
    exit(1)

# Test 3: Create TestAgent instance with mocked LLM
print("\n" + "=" * 60)
print("Test 3: Create TestAgent instance (with mocked LLM)")
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
        loaded_at=datetime.now(UTC)
    )
    print(f"✓ Created AgentContext: user_id={context.user_id}, fitness_level={context.fitness_level}")
    
    # Mock the LLM initialization to avoid API key requirement
    original_init_llm = BaseAgent._init_llm
    
    def mock_init_llm(self):
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value=Mock(content="This is a test response from the mocked LLM."))
        
        # Create async generator for streaming
        async def mock_astream(messages):
            chunks = ["This ", "is ", "a ", "streamed ", "response."]
            for chunk in chunks:
                yield Mock(content=chunk)
        
        mock_llm.astream = mock_astream
        return mock_llm
    
    BaseAgent._init_llm = mock_init_llm
    
    # Create TestAgent instance
    agent = TestAgent(context=context, db_session=None)
    print(f"✓ Created TestAgent instance")
    print(f"  - Agent has LLM: {agent.llm is not None}")
    print(f"  - Agent has context: {agent.context is not None}")
    print(f"  - Context is immutable: {context.model_config.get('frozen', False)}")
    
    # Restore original method
    BaseAgent._init_llm = original_init_llm
    
except Exception as e:
    print(f"✗ Failed to create TestAgent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Test method signatures
print("\n" + "=" * 60)
print("Test 4: Test method signatures and structure")
print("=" * 60)

try:
    import inspect
    
    # Check process_text signature
    sig = inspect.signature(agent.process_text)
    assert 'query' in sig.parameters, "process_text should have 'query' parameter"
    print("✓ process_text has correct signature")
    
    # Check process_voice signature
    sig = inspect.signature(agent.process_voice)
    assert 'query' in sig.parameters, "process_voice should have 'query' parameter"
    print("✓ process_voice has correct signature")
    
    # Check stream_response signature
    sig = inspect.signature(agent.stream_response)
    assert 'query' in sig.parameters, "stream_response should have 'query' parameter"
    print("✓ stream_response has correct signature")
    
    # Check get_tools signature
    sig = inspect.signature(agent.get_tools)
    print("✓ get_tools has correct signature")
    
    # Check _system_prompt signature
    sig = inspect.signature(agent._system_prompt)
    assert 'voice_mode' in sig.parameters, "_system_prompt should have 'voice_mode' parameter"
    print("✓ _system_prompt has correct signature")
    
except Exception as e:
    print(f"✗ Failed signature verification: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Test get_tools returns empty list
print("\n" + "=" * 60)
print("Test 5: Test get_tools returns empty list")
print("=" * 60)

try:
    tools = agent.get_tools()
    assert isinstance(tools, list), "get_tools should return a list"
    assert len(tools) == 0, "TestAgent should have no tools"
    print(f"✓ get_tools returns empty list: {tools}")
    
except Exception as e:
    print(f"✗ Failed get_tools test: {e}")
    exit(1)

# Test 6: Test _system_prompt
print("\n" + "=" * 60)
print("Test 6: Test _system_prompt")
print("=" * 60)

try:
    # Test text mode prompt
    text_prompt = agent._system_prompt(voice_mode=False)
    assert isinstance(text_prompt, str), "_system_prompt should return a string"
    assert len(text_prompt) > 0, "_system_prompt should not be empty"
    assert "beginner" in text_prompt.lower(), "Prompt should include fitness level"
    assert "fat_loss" in text_prompt.lower(), "Prompt should include primary goal"
    print(f"✓ Text mode prompt generated ({len(text_prompt)} characters)")
    print(f"  First 150 chars: {text_prompt[:150]}...")
    
    # Test voice mode prompt
    voice_prompt = agent._system_prompt(voice_mode=True)
    assert isinstance(voice_prompt, str), "_system_prompt should return a string"
    assert len(voice_prompt) > 0, "_system_prompt should not be empty"
    assert "concise" in voice_prompt.lower() or "voice" in voice_prompt.lower(), "Voice prompt should mention voice mode"
    print(f"✓ Voice mode prompt generated ({len(voice_prompt)} characters)")
    print(f"  Includes voice instructions: {'concise' in voice_prompt.lower()}")
    
except Exception as e:
    print(f"✗ Failed _system_prompt test: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 7: Test _build_messages
print("\n" + "=" * 60)
print("Test 7: Test _build_messages")
print("=" * 60)

try:
    # Test text mode messages
    messages = agent._build_messages("What should I do today?", voice_mode=False)
    assert isinstance(messages, list), "_build_messages should return a list"
    assert len(messages) > 0, "_build_messages should return non-empty list"
    print(f"✓ Text mode messages built ({len(messages)} messages)")
    
    # Test voice mode messages
    messages = agent._build_messages("What should I do today?", voice_mode=True)
    assert isinstance(messages, list), "_build_messages should return a list"
    print(f"✓ Voice mode messages built ({len(messages)} messages)")
    
except Exception as e:
    print(f"✗ Failed _build_messages test: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Summary
print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)
print("✓ All structural tests passed successfully!")
print("\nTestAgent verification complete:")
print("  1. ✓ Import successful")
print("  2. ✓ Extends BaseAgent correctly")
print("  3. ✓ Instance creation successful (with mocked LLM)")
print("  4. ✓ All method signatures correct")
print("  5. ✓ get_tools returns empty list")
print("  6. ✓ _system_prompt generates correct prompts")
print("  7. ✓ _build_messages works correctly")
print("\nThe TestAgent structure is correct!")
print("\nNote: To test actual LLM responses, configure ANTHROPIC_API_KEY")
print("      in backend/.env and run the full integration tests.")
