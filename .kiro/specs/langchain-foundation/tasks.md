# LangChain Foundation & Base Agent Framework - Tasks

## Task List

### 1. Setup and Dependencies

- [x] 1.1 Add LangChain dependencies to pyproject.toml
  - Add langchain ^0.3.0
  - Add langchain-core ^0.3.0
  - Add langchain-anthropic ^0.3.0
  - Add langchain-openai ^0.3.0
  - Add langchain-google-genai ^2.0.0

- [x] 1.2 Install dependencies and verify
  - Run `poetry install`
  - Verify LangChain imports work
  - Check version compatibility

### 2. Agent Context Models

- [x] 2.1 Create agents directory structure
  - Create `backend/app/agents/` directory
  - Create `backend/app/agents/__init__.py`

- [x] 2.2 Implement AgentContext model
  - Create `backend/app/agents/context.py`
  - Define AgentContext with all required fields
  - Set frozen=True for immutability
  - Add field descriptions and type hints
  - Add default values where appropriate

- [x] 2.3 Implement AgentResponse model
  - Add AgentResponse to context.py
  - Define content, agent_type, tools_used, metadata fields
  - Add type hints and descriptions

- [x] 2.4 Verify context models
  - Test import: `from app.agents.context import AgentContext`
  - Test AgentContext creation
  - Test immutability (should raise error on modification)

### 3. Base Agent Class

- [x] 3.1 Create BaseAgent abstract class
  - Create `backend/app/agents/base.py`
  - Define BaseAgent with ABC inheritance
  - Add __init__ method with context and db_session parameters

- [x] 3.2 Implement LLM initialization
  - Add _init_llm method
  - Support Anthropic provider
  - Support OpenAI provider
  - Support Google provider
  - Raise ValueError for unsupported providers

- [x] 3.3 Implement classifier LLM initialization
  - Add _init_classifier_llm method
  - Always use Claude Haiku
  - Set temperature=0.1, max_tokens=10

- [x] 3.4 Define abstract methods
  - Add process_text abstract method
  - Add process_voice abstract method
  - Add stream_response abstract method
  - Add get_tools abstract method
  - Add _system_prompt abstract method

- [x] 3.5 Implement message building
  - Add _build_messages method
  - Include system prompt
  - Add conversation history (limited by mode)
  - Add current query
  - Return list of LangChain messages

- [x] 3.6 Implement chat history formatting
  - Add _format_chat_history method
  - Convert conversation history to LangChain messages
  - Limit to last 10 messages

- [x] 3.7 Verify BaseAgent
  - Test import: `from app.agents.base import BaseAgent`
  - Verify abstract methods are defined
  - Test LLM initialization for each provider

### 4. Test Agent Implementation

- [x] 4.1 Create TestAgent class
  - Create `backend/app/agents/test_agent.py`
  - Extend BaseAgent
  - Import required dependencies

- [x] 4.2 Implement process_text method
  - Build messages with voice_mode=False
  - Call llm.ainvoke
  - Return AgentResponse with content

- [x] 4.3 Implement process_voice method
  - Build messages with voice_mode=True
  - Call llm.ainvoke
  - Return string content

- [x] 4.4 Implement stream_response method
  - Build messages
  - Use llm.astream
  - Yield chunks with content

- [x] 4.5 Implement get_tools method
  - Return empty list (no tools for test agent)

- [x] 4.6 Implement _system_prompt method
  - Create basic system prompt
  - Include user context (fitness_level, primary_goal)
  - Add voice mode instructions if applicable

- [x] 4.7 Verify TestAgent
  - Test import: `from app.agents.test_agent import TestAgent`
  - Create TestAgent instance
  - Test text response
  - Test voice response

### 5. Context Loader Service

- [x] 5.1 Create context_loader.py
  - Create `backend/app/services/context_loader.py`
  - Add imports for database models

- [x] 5.2 Implement load_agent_context function
  - Define async function with db, user_id, include_history parameters
  - Query UserProfile from database
  - Raise ValueError if profile not found
  - Call helper functions for workout/meal/history

- [x] 5.3 Implement _load_current_workout placeholder
  - Create async function
  - Return placeholder workout data
  - Add TODO comment for Sub-Doc 2

- [x] 5.4 Implement _load_current_meal placeholder
  - Create async function
  - Return placeholder meal data
  - Add TODO comment for Sub-Doc 2

- [x] 5.5 Implement _load_conversation_history placeholder
  - Create async function
  - Return empty list
  - Add TODO comment for Sub-Doc 3

- [x] 5.6 Build and return AgentContext
  - Assemble all loaded data
  - Create AgentContext instance
  - Log successful load
  - Return context

- [x] 5.7 Verify context loader
  - Test import: `from app.services.context_loader import load_agent_context`
  - Test with test user in database
  - Verify all fields populated
  - Test error handling for missing user

### 6. Agent Orchestrator

- [x] 6.1 Create AgentType enum
  - Create `backend/app/services/agent_orchestrator.py`
  - Define AgentType enum with all agent types
  - Include TEST type for testing

- [x] 6.2 Create AgentOrchestrator class
  - Define class with __init__ method
  - Accept db_session and mode parameters
  - Initialize caches based on mode
  - Initialize last_agent_type tracker

- [x] 6.3 Implement route_query method
  - Define async method with user_id, query, agent_type, voice_mode parameters
  - Load user context
  - Classify query if agent_type not provided
  - Get or create agent
  - Process based on mode
  - Return AgentResponse

- [x] 6.4 Implement _classify_query method (placeholder)
  - Check classification cache
  - Return AgentType.TEST (placeholder)
  - Cache result in voice mode
  - Add TODO comment for Sub-Doc 2

- [x] 6.5 Implement _get_or_create_agent method
  - Check agent cache if voice mode
  - Return cached agent if exists
  - Create new agent if not cached
  - Cache agent in voice mode

- [x] 6.6 Implement _create_agent factory method
  - Define agent_map with TEST agent
  - Add TODO comments for other agents
  - Get agent class from map
  - Create and return agent instance

- [x] 6.7 Implement warm_up method
  - Check if voice mode
  - Create test agent
  - Make dummy LLM call
  - Log success or warning
  - Handle errors gracefully

- [x] 6.8 Verify orchestrator
  - Test import: `from app.services.agent_orchestrator import AgentOrchestrator`
  - Create orchestrator instance
  - Test route_query in text mode
  - Test route_query in voice mode
  - Test warm_up method

### 7. Configuration Updates

- [x] 7.1 Add LLMProvider enum to config
  - Open `backend/app/core/config.py`
  - Define LLMProvider enum
  - Add ANTHROPIC, OPENAI, GOOGLE values

- [x] 7.2 Add LLM configuration fields
  - Add LLM_PROVIDER field with default
  - Add LLM_MODEL field
  - Add LLM_TEMPERATURE field
  - Add LLM_MAX_TOKENS field

- [x] 7.3 Add API key fields
  - Add ANTHROPIC_API_KEY optional field
  - Add OPENAI_API_KEY optional field
  - Add GOOGLE_API_KEY optional field

- [x] 7.4 Add classifier configuration
  - Add CLASSIFIER_MODEL field
  - Add CLASSIFIER_TEMPERATURE field

- [x] 7.5 Implement get_required_llm_api_key method
  - Check LLM_PROVIDER value
  - Return appropriate API key
  - Raise ValueError if key missing

- [x] 7.6 Update .env.example
  - Add LLM configuration section
  - Add example values for all fields
  - Add comments explaining each field

- [x] 7.7 Verify configuration
  - Test import: `from app.core.config import settings`
  - Test get_required_llm_api_key method
  - Verify all fields accessible

### 8. Integration Tests

- [x] 8.1 Create test file
  - Create `backend/tests/test_langchain_foundation.py`
  - Add imports for all components
  - Add pytest markers

- [x] 8.2 Write test_agent_context_creation
  - Create AgentContext instance
  - Assert all fields correct
  - Test immutability

- [x] 8.3 Write test_test_agent_text_response
  - Create AgentContext
  - Create TestAgent
  - Call process_text
  - Assert response is AgentResponse
  - Assert content is non-empty
  - Assert agent_type is "test"

- [x] 8.4 Write test_test_agent_voice_response
  - Create AgentContext
  - Create TestAgent
  - Call process_voice
  - Assert response is string
  - Assert content is non-empty

- [x] 8.5 Write test_context_loader
  - Use db_session and test_user fixtures
  - Call load_agent_context
  - Assert user_id matches
  - Assert fitness_level is valid
  - Assert primary_goal is not None

- [x] 8.6 Write test_agent_orchestrator_routing
  - Create AgentOrchestrator in text mode
  - Call route_query with TEST agent type
  - Assert response content is non-empty
  - Assert last_agent_type is TEST

- [x] 8.7 Write test_orchestrator_voice_mode
  - Create AgentOrchestrator in voice mode
  - Call warm_up
  - Call route_query with voice_mode=True
  - Assert response content is non-empty
  - Assert metadata mode is "voice"

- [x] 8.8 Run all tests
  - Execute: `poetry run pytest backend/tests/test_langchain_foundation.py -v`
  - Verify all tests pass
  - Check test coverage

### 9. Documentation and Verification

- [x] 9.1 Add docstrings to all modules
  - Verify all classes have docstrings
  - Verify all methods have docstrings
  - Add parameter descriptions
  - Add return value descriptions

- [ ] 9.2 Run verification commands
  - Test dependency installation
  - Test all module imports
  - Test configuration
  - Run integration tests

- [ ] 9.3 Update README if needed
  - Document new dependencies
  - Document configuration requirements
  - Add usage examples

- [ ] 9.4 Final verification checklist
  - All dependencies installed
  - All modules importable
  - All tests passing
  - Configuration complete
  - Documentation complete

---

## Task Dependencies

```
1.1 → 1.2
2.1 → 2.2 → 2.3 → 2.4
3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7
4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6 → 4.7
5.1 → 5.2 → 5.3 → 5.4 → 5.5 → 5.6 → 5.7
6.1 → 6.2 → 6.3 → 6.4 → 6.5 → 6.6 → 6.7 → 6.8
7.1 → 7.2 → 7.3 → 7.4 → 7.5 → 7.6 → 7.7
8.1 → 8.2 → 8.3 → 8.4 → 8.5 → 8.6 → 8.7 → 8.8
9.1 → 9.2 → 9.3 → 9.4

Critical Path: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

---

## Estimated Time

- **Section 1 (Setup):** 0.5 days
- **Section 2 (Context Models):** 0.5 days
- **Section 3 (Base Agent):** 1 day
- **Section 4 (Test Agent):** 0.5 days
- **Section 5 (Context Loader):** 0.5 days
- **Section 6 (Orchestrator):** 1 day
- **Section 7 (Configuration):** 0.5 days
- **Section 8 (Tests):** 1 day
- **Section 9 (Documentation):** 0.5 days

**Total:** 5-6 days

---

## Notes

- Tasks marked with TODO comments are placeholders for future sub-docs
- All async functions must use `await` for database operations
- All tests must use `@pytest.mark.asyncio` decorator
- Configuration must be validated before use
- Error handling should be comprehensive with logging

---

## Success Criteria

All tasks complete when:
- ✅ All checkboxes marked complete
- ✅ All verification commands pass
- ✅ All integration tests pass
- ✅ Code review approved
- ✅ Documentation complete
