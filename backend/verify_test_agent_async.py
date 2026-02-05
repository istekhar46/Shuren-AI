"""
Async verification script for TestAgent implementation.

This script tests the async methods of TestAgent with mocked LLM:
1. Test process_text async method
2. Test process_voice async method
3. Test stream_response async generator
"""

import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, UTC

from app.agents.test_agent import TestAgent
from app.agents.base import BaseAgent
from app.agents.context import AgentContext, AgentResponse


async def main():
    """Run async verification tests."""
    
    print("=" * 60)
    print("Async TestAgent Verification")
    print("=" * 60)
    
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
    
    # Mock the LLM initialization
    original_init_llm = BaseAgent._init_llm
    
    def mock_init_llm(self):
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value=Mock(
            content="This is a test response. Your fitness level is beginner and your goal is fat loss."
        ))
        
        # Create async generator for streaming
        async def mock_astream(messages):
            chunks = ["This ", "is ", "a ", "streamed ", "response ", "for ", "testing."]
            for chunk in chunks:
                yield Mock(content=chunk)
        
        mock_llm.astream = mock_astream
        return mock_llm
    
    BaseAgent._init_llm = mock_init_llm
    
    # Create TestAgent instance
    agent = TestAgent(context=context, db_session=None)
    print(f"✓ Created TestAgent instance with mocked LLM\n")
    
    # Test 1: process_text
    print("=" * 60)
    print("Test 1: process_text async method")
    print("=" * 60)
    
    try:
        query = "What is my fitness level?"
        print(f"Query: {query}")
        
        response = await agent.process_text(query)
        
        print(f"✓ Received text response")
        print(f"  - Response type: {type(response).__name__}")
        print(f"  - Is AgentResponse: {isinstance(response, AgentResponse)}")
        print(f"  - Agent type: {response.agent_type}")
        print(f"  - Content length: {len(response.content)} characters")
        print(f"  - Tools used: {response.tools_used}")
        print(f"  - Metadata keys: {list(response.metadata.keys())}")
        print(f"\n  Response content:")
        print(f"  {response.content}")
        
        # Verify response structure
        assert isinstance(response, AgentResponse), "Should return AgentResponse"
        assert response.agent_type == "test", "Agent type should be 'test'"
        assert len(response.content) > 0, "Response content should not be empty"
        assert isinstance(response.tools_used, list), "Tools used should be a list"
        assert isinstance(response.metadata, dict), "Metadata should be a dict"
        assert "mode" in response.metadata, "Metadata should include mode"
        assert response.metadata["mode"] == "text", "Mode should be 'text'"
        print("\n✓ Text response validation passed")
        
    except Exception as e:
        print(f"✗ Failed process_text test: {e}")
        import traceback
        traceback.print_exc()
        BaseAgent._init_llm = original_init_llm
        exit(1)
    
    # Test 2: process_voice
    print("\n" + "=" * 60)
    print("Test 2: process_voice async method")
    print("=" * 60)
    
    try:
        query = "What should I focus on today?"
        print(f"Query: {query}")
        
        response = await agent.process_voice(query)
        
        print(f"✓ Received voice response")
        print(f"  - Response type: {type(response).__name__}")
        print(f"  - Is string: {isinstance(response, str)}")
        print(f"  - Content length: {len(response)} characters")
        print(f"\n  Response content:")
        print(f"  {response}")
        
        # Verify response structure
        assert isinstance(response, str), "Voice response should be a string"
        assert len(response) > 0, "Voice response should not be empty"
        print("\n✓ Voice response validation passed")
        
    except Exception as e:
        print(f"✗ Failed process_voice test: {e}")
        import traceback
        traceback.print_exc()
        BaseAgent._init_llm = original_init_llm
        exit(1)
    
    # Test 3: stream_response
    print("\n" + "=" * 60)
    print("Test 3: stream_response async generator")
    print("=" * 60)
    
    try:
        query = "Tell me about my workout plan"
        print(f"Query: {query}")
        
        chunks = []
        print(f"\n  Streaming response:")
        print(f"  ", end="")
        
        async for chunk in agent.stream_response(query):
            chunks.append(chunk)
            print(chunk, end="", flush=True)
        
        print()  # New line after streaming
        
        print(f"\n✓ Received streamed response")
        print(f"  - Number of chunks: {len(chunks)}")
        print(f"  - Total length: {len(''.join(chunks))} characters")
        print(f"  - Full response: {''.join(chunks)}")
        
        # Verify streaming
        assert len(chunks) > 0, "Should receive at least one chunk"
        assert all(isinstance(chunk, str) for chunk in chunks), "All chunks should be strings"
        print("\n✓ Stream response validation passed")
        
    except Exception as e:
        print(f"✗ Failed stream_response test: {e}")
        import traceback
        traceback.print_exc()
        BaseAgent._init_llm = original_init_llm
        exit(1)
    
    # Restore original method
    BaseAgent._init_llm = original_init_llm
    
    # Summary
    print("\n" + "=" * 60)
    print("ASYNC VERIFICATION SUMMARY")
    print("=" * 60)
    print("✓ All async tests passed successfully!")
    print("\nTestAgent async methods verified:")
    print("  1. ✓ process_text returns AgentResponse")
    print("  2. ✓ process_voice returns string")
    print("  3. ✓ stream_response yields chunks")
    print("\nThe TestAgent is fully functional!")


if __name__ == "__main__":
    asyncio.run(main())
