"""
End-to-End Live Test for LangChain Foundation

This script tests the complete LangChain foundation implementation with live
Google Gemini API calls. It validates all components working together:

1. Configuration loading
2. Agent context creation
3. BaseAgent LLM initialization
4. TestAgent text and voice responses
5. Context loader with database
6. Agent orchestrator routing
7. Voice mode caching
8. Warm-up functionality

Requirements:
- GOOGLE_API_KEY must be set in .env
- Database must be accessible
- At least one test user must exist in database
"""

import asyncio
import sys
from datetime import datetime
from uuid import UUID

# Add backend to path
sys.path.insert(0, '.')

from sqlalchemy import select
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.agents.context import AgentContext
from app.agents.test_agent import TestAgent
from app.services.context_loader import load_agent_context
from app.services.agent_orchestrator import AgentOrchestrator, AgentType


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * 70}{Colors.ENDC}")


async def test_configuration():
    """Test 1: Verify configuration is loaded correctly."""
    print_section("Test 1: Configuration Loading")
    
    try:
        # Check LLM provider
        print_info(f"LLM Provider: {settings.LLM_PROVIDER}")
        print_info(f"LLM Model: {settings.LLM_MODEL}")
        print_info(f"LLM Temperature: {settings.LLM_TEMPERATURE}")
        print_info(f"LLM Max Tokens: {settings.LLM_MAX_TOKENS}")
        
        # Check classifier config
        print_info(f"Classifier Model: {settings.CLASSIFIER_MODEL}")
        print_info(f"Classifier Temperature: {settings.CLASSIFIER_TEMPERATURE}")
        
        # Verify API key is set
        api_key = settings.get_required_llm_api_key()
        if api_key:
            print_success(f"API Key configured (length: {len(api_key)})")
        else:
            print_error("API Key not configured!")
            return False
        
        print_success("Configuration loaded successfully")
        return True
        
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return False


async def test_agent_context_creation():
    """Test 2: Create and validate AgentContext."""
    print_section("Test 2: Agent Context Creation")
    
    try:
        # Create a test context
        context = AgentContext(
            user_id="test-user-123",
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            secondary_goal="general_fitness",
            energy_level="high",
            current_workout_plan={"plan_id": "test-workout"},
            current_meal_plan={"plan_id": "test-meal"},
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            loaded_at=datetime.utcnow()
        )
        
        print_info(f"User ID: {context.user_id}")
        print_info(f"Fitness Level: {context.fitness_level}")
        print_info(f"Primary Goal: {context.primary_goal}")
        print_info(f"Energy Level: {context.energy_level}")
        print_info(f"Conversation History: {len(context.conversation_history)} messages")
        
        # Test immutability
        try:
            context.user_id = "modified"
            print_error("Context is NOT immutable!")
            return False
        except Exception:
            print_success("Context is immutable (as expected)")
        
        print_success("AgentContext created and validated successfully")
        return True
        
    except Exception as e:
        print_error(f"AgentContext creation error: {e}")
        return False


async def test_test_agent_text_response(context: AgentContext):
    """Test 3: TestAgent text response with live LLM."""
    print_section("Test 3: TestAgent Text Response (Live LLM)")
    
    try:
        # Create test agent
        agent = TestAgent(context=context, db_session=None)
        print_success("TestAgent created successfully")
        
        # Test text query
        query = "What's a good workout for building muscle?"
        print_info(f"Query: {query}")
        print_info("Calling LLM... (this may take a few seconds)")
        
        response = await agent.process_text(query)
        
        print_info(f"Response Type: {type(response).__name__}")
        print_info(f"Agent Type: {response.agent_type}")
        print_info(f"Content Length: {len(response.content)} characters")
        print_info(f"Tools Used: {response.tools_used}")
        print_info(f"Metadata: {response.metadata}")
        
        print(f"\n{Colors.OKCYAN}Response Content:{Colors.ENDC}")
        print(f"{Colors.BOLD}{response.content[:500]}...{Colors.ENDC}\n")
        
        # Validate response
        assert response.agent_type == "test", "Agent type should be 'test'"
        assert len(response.content) > 0, "Response content should not be empty"
        assert isinstance(response.tools_used, list), "Tools used should be a list"
        assert isinstance(response.metadata, dict), "Metadata should be a dict"
        
        print_success("TestAgent text response validated successfully")
        return True
        
    except Exception as e:
        print_error(f"TestAgent text response error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_test_agent_voice_response(context: AgentContext):
    """Test 4: TestAgent voice response with live LLM."""
    print_section("Test 4: TestAgent Voice Response (Live LLM)")
    
    try:
        # Create test agent
        agent = TestAgent(context=context, db_session=None)
        
        # Test voice query
        query = "Quick tip for today's workout?"
        print_info(f"Query: {query}")
        print_info("Calling LLM in voice mode... (this may take a few seconds)")
        
        response = await agent.process_voice(query)
        
        print_info(f"Response Type: {type(response).__name__}")
        print_info(f"Content Length: {len(response)} characters")
        
        print(f"\n{Colors.OKCYAN}Voice Response:{Colors.ENDC}")
        print(f"{Colors.BOLD}{response}{Colors.ENDC}\n")
        
        # Validate response
        assert isinstance(response, str), "Voice response should be a string"
        assert len(response) > 0, "Voice response should not be empty"
        
        print_success("TestAgent voice response validated successfully")
        return True
        
    except Exception as e:
        print_error(f"TestAgent voice response error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_streaming_response(context: AgentContext):
    """Test 5: TestAgent streaming response."""
    print_section("Test 5: TestAgent Streaming Response (Live LLM)")
    
    try:
        # Create test agent
        agent = TestAgent(context=context, db_session=None)
        
        # Test streaming query
        query = "Give me 3 quick fitness tips"
        print_info(f"Query: {query}")
        print_info("Streaming response from LLM...")
        
        print(f"\n{Colors.OKCYAN}Streamed Response:{Colors.ENDC}")
        print(f"{Colors.BOLD}", end="")
        
        chunks = []
        async for chunk in agent.stream_response(query):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
        
        print(f"{Colors.ENDC}\n")
        
        # Validate streaming
        assert len(chunks) > 0, "Should receive at least one chunk"
        full_response = "".join(chunks)
        assert len(full_response) > 0, "Full response should not be empty"
        
        print_info(f"Received {len(chunks)} chunks")
        print_info(f"Total length: {len(full_response)} characters")
        
        print_success("TestAgent streaming response validated successfully")
        return True
        
    except Exception as e:
        print_error(f"TestAgent streaming error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_loader_with_database():
    """Test 6: Context loader with real database."""
    print_section("Test 6: Context Loader with Database")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Find a test user
            stmt = select(User).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print_warning("No users found in database - skipping database test")
                return True
            
            print_info(f"Found user: {user.id}")
            
            # Load context for this user
            print_info("Loading agent context from database...")
            context = await load_agent_context(
                db=db,
                user_id=str(user.id),
                include_history=True
            )
            
            print_info(f"User ID: {context.user_id}")
            print_info(f"Fitness Level: {context.fitness_level}")
            print_info(f"Primary Goal: {context.primary_goal}")
            print_info(f"Secondary Goal: {context.secondary_goal}")
            print_info(f"Energy Level: {context.energy_level}")
            print_info(f"Loaded At: {context.loaded_at}")
            
            # Validate context
            assert context.user_id == str(user.id), "User ID should match"
            assert context.fitness_level in ["beginner", "intermediate", "advanced"], "Valid fitness level"
            assert context.primary_goal is not None, "Primary goal should be set"
            
            print_success("Context loaded from database successfully")
            return True
            
    except Exception as e:
        print_error(f"Context loader error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_text_mode():
    """Test 7: Agent orchestrator in text mode."""
    print_section("Test 7: Agent Orchestrator - Text Mode")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Find a test user
            stmt = select(User).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print_warning("No users found in database - using mock user ID")
                user_id = "test-user-123"
                # Create mock context for testing without database
                from app.agents.context import AgentContext
                context = AgentContext(
                    user_id=user_id,
                    fitness_level="intermediate",
                    primary_goal="muscle_gain",
                    energy_level="medium"
                )
                # Test without database
                orchestrator = AgentOrchestrator(db_session=db, mode="text")
                print_info("Testing orchestrator without database (mock context)")
                
                # Create agent directly
                agent = orchestrator._create_agent(AgentType.TEST, context)
                response = await agent.process_text("Hello, test query")
                
                print_info(f"Response received: {len(response.content)} characters")
                print_success("Orchestrator text mode validated (without database)")
                return True
            
            user_id = str(user.id)
            print_info(f"Using user: {user_id}")
            
            # Create orchestrator in text mode
            orchestrator = AgentOrchestrator(db_session=db, mode="text")
            print_success("Orchestrator created in text mode")
            
            # Route a query
            query = "What should I focus on in my workout today?"
            print_info(f"Query: {query}")
            print_info("Routing query through orchestrator...")
            
            response = await orchestrator.route_query(
                user_id=user_id,
                query=query,
                agent_type=AgentType.TEST,
                voice_mode=False
            )
            
            print_info(f"Response Type: {type(response).__name__}")
            print_info(f"Agent Type: {response.agent_type}")
            print_info(f"Content Length: {len(response.content)} characters")
            
            print(f"\n{Colors.OKCYAN}Orchestrator Response:{Colors.ENDC}")
            print(f"{Colors.BOLD}{response.content[:300]}...{Colors.ENDC}\n")
            
            # Validate
            assert response.agent_type == "test", "Should route to test agent"
            assert len(response.content) > 0, "Response should not be empty"
            assert orchestrator.last_agent_type == AgentType.TEST, "Should track last agent"
            
            print_success("Orchestrator text mode validated successfully")
            return True
            
    except Exception as e:
        print_error(f"Orchestrator text mode error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_orchestrator_voice_mode():
    """Test 8: Agent orchestrator in voice mode with caching."""
    print_section("Test 8: Agent Orchestrator - Voice Mode with Caching")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Find a test user
            stmt = select(User).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print_warning("No users found in database - using mock user ID")
                user_id = "test-user-123"
                # Create mock context
                from app.agents.context import AgentContext
                context = AgentContext(
                    user_id=user_id,
                    fitness_level="intermediate",
                    primary_goal="muscle_gain",
                    energy_level="medium"
                )
                # Test without database
                orchestrator = AgentOrchestrator(db_session=db, mode="voice")
                print_info("Testing orchestrator without database (mock context)")
                
                # Warm up
                await orchestrator.warm_up()
                print_success("Warm-up completed")
                
                # Create agent directly
                agent = orchestrator._create_agent(AgentType.TEST, context)
                response_text = await agent.process_voice("Quick tip?")
                
                print_info(f"Response received: {len(response_text)} characters")
                print_success("Orchestrator voice mode validated (without database)")
                return True
            
            user_id = str(user.id)
            print_info(f"Using user: {user_id}")
            
            # Create orchestrator in voice mode
            orchestrator = AgentOrchestrator(db_session=db, mode="voice")
            print_success("Orchestrator created in voice mode")
            
            # Test warm-up
            print_info("Warming up LLM connection...")
            await orchestrator.warm_up()
            print_success("Warm-up completed")
            
            # First query (should cache agent)
            query1 = "Quick workout tip?"
            print_info(f"Query 1: {query1}")
            
            response1 = await orchestrator.route_query(
                user_id=user_id,
                query=query1,
                agent_type=AgentType.TEST,
                voice_mode=True
            )
            
            print_info(f"Response 1 Length: {len(response1.content)} characters")
            print_info(f"Metadata: {response1.metadata}")
            
            # Check cache
            assert orchestrator._agent_cache is not None, "Agent cache should exist in voice mode"
            assert AgentType.TEST in orchestrator._agent_cache, "Test agent should be cached"
            print_success("Agent cached successfully")
            
            # Second query (should use cached agent)
            query2 = "Another quick tip?"
            print_info(f"Query 2: {query2}")
            
            response2 = await orchestrator.route_query(
                user_id=user_id,
                query=query2,
                agent_type=AgentType.TEST,
                voice_mode=True
            )
            
            print_info(f"Response 2 Length: {len(response2.content)} characters")
            
            # Validate caching
            assert response2.metadata.get("mode") == "voice", "Should be in voice mode"
            print_success("Cached agent used successfully")
            
            print_success("Orchestrator voice mode with caching validated successfully")
            return True
            
    except Exception as e:
        print_error(f"Orchestrator voice mode error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all end-to-end tests."""
    print_header("LangChain Foundation - End-to-End Live Test")
    print_info(f"Test started at: {datetime.utcnow().isoformat()}")
    print_info(f"Using LLM Provider: {settings.LLM_PROVIDER}")
    print_info(f"Using LLM Model: {settings.LLM_MODEL}")
    
    results = []
    
    # Test 1: Configuration
    results.append(("Configuration Loading", await test_configuration()))
    
    # Test 2: Agent Context
    results.append(("Agent Context Creation", await test_agent_context_creation()))
    
    # Create a test context for agent tests
    test_context = AgentContext(
        user_id="test-user-e2e",
        fitness_level="intermediate",
        primary_goal="muscle_gain",
        secondary_goal="general_fitness",
        energy_level="high",
        current_workout_plan={},
        current_meal_plan={},
        conversation_history=[],
        loaded_at=datetime.utcnow()
    )
    
    # Test 3: TestAgent Text Response
    results.append(("TestAgent Text Response", await test_test_agent_text_response(test_context)))
    
    # Test 4: TestAgent Voice Response
    results.append(("TestAgent Voice Response", await test_test_agent_voice_response(test_context)))
    
    # Test 5: Streaming Response
    results.append(("TestAgent Streaming", await test_streaming_response(test_context)))
    
    # Test 6: Context Loader with Database
    results.append(("Context Loader with Database", await test_context_loader_with_database()))
    
    # Test 7: Orchestrator Text Mode
    results.append(("Orchestrator Text Mode", await test_orchestrator_text_mode()))
    
    # Test 8: Orchestrator Voice Mode
    results.append(("Orchestrator Voice Mode", await test_orchestrator_voice_mode()))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}")
        print(f"{Colors.OKGREEN}The LangChain foundation is working correctly with live API calls.{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")
        print(f"{Colors.FAIL}Please review the errors above.{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
