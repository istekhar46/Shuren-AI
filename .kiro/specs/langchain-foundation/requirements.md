# LangChain Foundation & Base Agent Framework - Requirements

## Spec Information
**Feature:** LangChain Foundation & Base Agent Framework  
**Version:** 1.0  
**Status:** Ready for Implementation  
**Source Document:** [01-LANGCHAIN-FOUNDATION.md](../../../docs/technichal/phase-2-breakdown/01-LANGCHAIN-FOUNDATION.md)  
**Dependencies:** Phase 1 (Database, Models, Auth)  
**Estimated Effort:** 3-5 days

---

## Overview

Establish the foundational LangChain infrastructure for the Shuren AI fitness coaching system. This includes the base agent framework, context management, agent orchestration, and multi-provider LLM support that will be used by all specialized agents in Phase 2.

---

## User Stories

### US-1: Agent Context Management
**As a** developer  
**I want** an immutable context model that contains all user data needed for agent interactions  
**So that** agents can make informed decisions without repeated database queries

**Acceptance Criteria:**
- AgentContext model is created with Pydantic
- Context includes user_id, fitness_level, primary_goal, secondary_goal, energy_level
- Context includes current_workout_plan and current_meal_plan (cached)
- Context includes conversation_history (last N messages)
- Context is immutable (frozen=True)
- AgentResponse model standardizes agent outputs

### US-2: Base Agent Framework
**As a** developer  
**I want** a base agent class that all specialized agents can extend  
**So that** we have consistent LLM integration and message handling across all agents

**Acceptance Criteria:**
- BaseAgent abstract class is created
- Supports multi-provider LLM initialization (Anthropic, OpenAI, Google)
- Provides abstract methods: process_text, process_voice, stream_response, get_tools, _system_prompt
- Implements message building with conversation history
- Implements chat history formatting for LangChain
- Includes fast classifier LLM for query routing (Claude Haiku)

### US-3: Test Agent Implementation
**As a** developer  
**I want** a simple test agent to verify the framework  
**So that** I can validate the base agent functionality before building specialized agents

**Acceptance Criteria:**
- TestAgent extends BaseAgent
- Implements all required abstract methods
- Can respond to text queries
- Can respond to voice queries (concise)
- Can stream responses
- Has appropriate system prompt for testing

### US-4: Context Loading Service
**As a** developer  
**I want** a service that loads user context from the database  
**So that** agents have access to all necessary user data

**Acceptance Criteria:**
- load_agent_context function loads UserProfile from database
- Loads current workout plan (placeholder for Sub-Doc 2)
- Loads current meal plan (placeholder for Sub-Doc 2)
- Loads conversation history (placeholder for Sub-Doc 3)
- Raises ValueError if user not found
- Returns complete AgentContext object

### US-5: Agent Orchestrator
**As a** developer  
**I want** an orchestrator that routes queries to appropriate agents  
**So that** user queries are handled by the right specialized agent

**Acceptance Criteria:**
- AgentOrchestrator class manages agent routing
- Supports text and voice modes
- Loads user context from database
- Classifies queries to determine agent type (placeholder for Sub-Doc 2)
- Routes to appropriate agent
- Caches agents in voice mode for performance
- Caches classifications in voice mode
- Tracks last agent type used
- Provides warm_up method for LLM connection pre-warming

### US-6: Multi-Provider LLM Support
**As a** developer  
**I want** support for multiple LLM providers  
**So that** we can switch between Anthropic, OpenAI, and Google based on needs

**Acceptance Criteria:**
- Configuration supports LLM_PROVIDER enum (anthropic, openai, google)
- Configuration includes LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
- Configuration includes API keys for all providers
- BaseAgent initializes correct LLM based on provider
- get_required_llm_api_key validates API key for chosen provider
- Classifier always uses Claude Haiku for fast routing

### US-7: Integration Testing
**As a** developer  
**I want** comprehensive integration tests  
**So that** I can verify the foundation works correctly

**Acceptance Criteria:**
- Test agent context creation
- Test agent text response
- Test agent voice response
- Test context loader with database
- Test orchestrator routing
- Test orchestrator voice mode
- All tests pass with pytest

---

## Technical Requirements

### TR-1: Dependencies
- LangChain 0.3.0+
- LangChain Core 0.3.0+
- LangChain Anthropic 0.3.0+
- LangChain OpenAI 0.3.0+
- LangChain Google GenAI 2.0.0+

### TR-2: File Structure
```
backend/app/
├── agents/
│   ├── __init__.py
│   ├── context.py          # AgentContext, AgentResponse models
│   ├── base.py             # BaseAgent abstract class
│   └── test_agent.py       # TestAgent implementation
├── services/
│   ├── context_loader.py   # load_agent_context function
│   └── agent_orchestrator.py  # AgentOrchestrator class
└── core/
    └── config.py           # Updated with LLM settings
```

### TR-3: Configuration
- Add LLMProvider enum to config
- Add LLM configuration fields
- Add API key fields for all providers
- Add classifier configuration
- Update .env.example with LLM settings

### TR-4: Database Integration
- Use existing UserProfile model
- Query profile asynchronously
- Handle missing profiles gracefully
- Placeholder functions for workout/meal loading

### TR-5: Performance
- Voice mode caches agents in memory
- Voice mode caches query classifications
- Classifier uses fast model (Claude Haiku)
- Context loaded once per interaction

---

## Non-Functional Requirements

### NFR-1: Code Quality
- All code follows PEP 8 style guide
- Type hints on all functions
- Comprehensive docstrings
- Abstract methods clearly documented

### NFR-2: Error Handling
- ValueError for missing users
- ValueError for unsupported LLM providers
- Graceful handling of API key errors
- Logging for all major operations

### NFR-3: Testing
- Unit tests for all components
- Integration tests for end-to-end flows
- Test coverage >80%
- All tests use pytest with async support

### NFR-4: Documentation
- Inline code comments for complex logic
- Docstrings for all classes and methods
- README updates if needed
- Verification steps documented

---

## Verification Steps

### Step 1: Dependency Installation
```bash
cd backend
poetry install
poetry run python -c "import langchain; print(f'LangChain {langchain.__version__}')"
```

### Step 2: Module Imports
```bash
poetry run python -c "from app.agents.context import AgentContext; print('✓ Context model OK')"
poetry run python -c "from app.agents.base import BaseAgent; print('✓ Base agent OK')"
poetry run python -c "from app.agents.test_agent import TestAgent; print('✓ Test agent OK')"
poetry run python -c "from app.services.context_loader import load_agent_context; print('✓ Context loader OK')"
poetry run python -c "from app.services.agent_orchestrator import AgentOrchestrator; print('✓ Orchestrator OK')"
```

### Step 3: Configuration
```bash
poetry run python -c "from app.core.config import settings; settings.get_required_llm_api_key(); print('✓ Config OK')"
```

### Step 4: Integration Tests
```bash
poetry run pytest backend/tests/test_langchain_foundation.py -v
```

---

## Success Criteria

This spec is complete when:

✅ All dependencies installed successfully  
✅ All modules can be imported without errors  
✅ AgentContext and AgentResponse models work correctly  
✅ BaseAgent provides proper abstraction  
✅ TestAgent can respond to queries  
✅ Context loader retrieves user data from database  
✅ AgentOrchestrator routes queries correctly  
✅ Both text and voice modes work  
✅ All integration tests pass  
✅ Configuration supports all three LLM providers  

---

## Out of Scope

The following are explicitly NOT part of this spec:
- Specialized agent implementations (Sub-Doc 2)
- Actual workout/meal plan loading (Sub-Doc 2)
- Conversation history persistence (Sub-Doc 3)
- Text chat API endpoints (Sub-Doc 3)
- LiveKit integration (Sub-Doc 4, 5)
- Voice optimization (Sub-Doc 6)

---

## Dependencies

### Prerequisites
- Phase 1 must be complete
- Database models (User, UserProfile) must exist
- Async database session must be configured
- Redis must be configured (for future caching)

### Blocks
This spec blocks:
- Sub-Doc 2: Specialized Agents (depends on BaseAgent)
- Sub-Doc 3: Text Chat API (depends on AgentOrchestrator)
- Sub-Doc 5: Voice Agent (depends on AgentOrchestrator)

---

## Notes

- The TestAgent is intentionally simple - just validates the framework
- Actual query classification will be implemented in Sub-Doc 2
- Workout/meal loading are placeholders - will be implemented in Sub-Doc 2
- Conversation history loading is a placeholder - will be implemented in Sub-Doc 3
- Voice mode caching is critical for <2s latency requirement
- Classifier must use fast model (Haiku) to minimize routing overhead

---

## References

- [01-LANGCHAIN-FOUNDATION.md](../../../docs/technichal/phase-2-breakdown/01-LANGCHAIN-FOUNDATION.md) - Source document
- [TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md](../../../docs/technichal/TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md) - Parent TRD
- [LangChain Documentation](https://python.langchain.com) - LangChain reference
