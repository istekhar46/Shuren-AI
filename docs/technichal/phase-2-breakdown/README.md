# Phase 2: AI Integration - Implementation Guide

## Overview

This directory contains the complete breakdown of Phase 2 (AI Integration) into 6 manageable sub-documents. Each sub-doc represents a logical implementation unit with clear dependencies, verification steps, and success criteria.

Phase 2 implements the **Hybrid LiveKit + LangChain Agent Architecture** for AI-powered fitness coaching with both voice and text interactions.

## Quick Start

1. **Read the Overview**: Start with [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)
2. **Verify Phase 1**: Ensure Phase 1 (Foundation) is complete
3. **Follow the Sequence**: Implement sub-docs in order (1→2→3/4→5→6)
4. **Verify Each Step**: Run verification tests after each sub-doc
5. **Create Specs**: Use Kiro's spec workflow to create implementation specs for each sub-doc

---

## Sub-Documents

### [00-PHASE-2-OVERVIEW.md](./00-PHASE-2-OVERVIEW.md)
**Purpose:** High-level roadmap and success criteria for Phase 2  
**Read First:** Yes - provides context for all other sub-docs  
**Key Content:**
- Phase 1 completion verification
- Phase 2 objectives and goals
- Implementation sequence and dependencies
- Success criteria for entire phase
- Risk mitigation strategies

---

### [01-LANGCHAIN-FOUNDATION.md](./01-LANGCHAIN-FOUNDATION.md)
**Purpose:** Core LangChain setup and base agent framework  
**Dependencies:** Phase 1 (Database, Models, Auth)  
**Estimated Time:** 3-5 days  

**What You'll Build:**
- `AgentContext` model for immutable user context
- `BaseAgent` abstract class with LLM integration
- `TestAgent` for framework verification
- `AgentOrchestrator` for query routing
- Context loader service for database integration
- Multi-provider LLM support (Anthropic, OpenAI, Google)

**Key Files Created:**
- `backend/app/agents/context.py`
- `backend/app/agents/base.py`
- `backend/app/agents/test_agent.py`
- `backend/app/services/agent_orchestrator.py`
- `backend/app/services/context_loader.py`

**Verification:**
```bash
poetry run pytest backend/tests/test_langchain_foundation.py -v
```

**Success Criteria:**
- ✅ Test agent responds to queries
- ✅ Orchestrator routes to test agent
- ✅ Context loads from database
- ✅ Both text and voice modes work

---

### [02-SPECIALIZED-AGENTS.md](./02-SPECIALIZED-AGENTS.md)
**Purpose:** Implement 6 specialized AI agents with domain expertise  
**Dependencies:** Sub-Doc 1 (LangChain Foundation)  
**Estimated Time:** 5-7 days  

**What You'll Build:**
1. **Workout Planner Agent** - Exercise plans, form guidance, demonstrations
2. **Diet Planner Agent** - Meal plans, nutrition, recipes
3. **Supplement Guidance Agent** - Supplement information (non-medical)
4. **Tracking & Adjustment Agent** - Progress tracking, plan adjustments
5. **Scheduling & Reminder Agent** - Schedule management, timing
6. **General Assistant Agent** - Motivation, casual conversation

**Key Features Per Agent:**
- Domain-specific tools (LangChain `@tool` decorated functions)
- Specialized system prompts
- Database integration for user data
- Support for both text and voice modes

**Key Files Created:**
- `backend/app/agents/workout_planner.py`
- `backend/app/agents/diet_planner.py`
- `backend/app/agents/supplement_guide.py`
- `backend/app/agents/tracker.py`
- `backend/app/agents/scheduler.py`
- `backend/app/agents/general_assistant.py`

**Verification:**
```bash
poetry run pytest backend/tests/test_specialized_agents.py -v
```

**Success Criteria:**
- ✅ All 6 agents implemented with working tools
- ✅ Orchestrator routes correctly to each agent
- ✅ Classification works accurately
- ✅ All tests pass

---

### [03-TEXT-CHAT-API.md](./03-TEXT-CHAT-API.md)
**Purpose:** REST API endpoints for text-based chat interactions  
**Dependencies:** Sub-Doc 1, Sub-Doc 2  
**Estimated Time:** 2-3 days  
**Can Run in Parallel With:** Sub-Doc 4 (LiveKit Infrastructure)

**What You'll Build:**
- Synchronous chat endpoint (`POST /api/v1/chat/chat`)
- Streaming chat endpoint (`POST /api/v1/chat/stream`) with Server-Sent Events
- Conversation history persistence
- Chat history retrieval and management

**Key Files Created:**
- `backend/app/models/conversation.py` - Conversation history model
- `backend/app/schemas/chat.py` - Chat request/response schemas
- `backend/app/api/v1/endpoints/chat.py` - Chat endpoints
- Database migration for conversation_messages table

**Verification:**
```bash
poetry run pytest backend/tests/test_chat_endpoints.py -v
```

**Success Criteria:**
- ✅ Chat endpoints working
- ✅ Streaming functional
- ✅ History persisted
- ✅ All tests pass

---

### [04-LIVEKIT-INFRASTRUCTURE.md](./04-LIVEKIT-INFRASTRUCTURE.md)
**Purpose:** LiveKit server setup and room management  
**Dependencies:** Phase 1 (Auth), Sub-Doc 1 (Foundation)  
**Estimated Time:** 2-3 days  
**Can Run in Parallel With:** Sub-Doc 3 (Text Chat API)

**What You'll Build:**
- LiveKit server configuration (cloud or self-hosted)
- Room creation and management
- Access token generation
- FastAPI endpoints for voice session lifecycle

**Key Files Created:**
- `backend/app/core/livekit_client.py` - LiveKit API client
- `backend/app/schemas/voice_session.py` - Voice session schemas
- `backend/app/api/v1/endpoints/voice_sessions.py` - Voice session endpoints
- `livekit.yaml` - LiveKit server configuration (if self-hosted)

**Verification:**
```bash
poetry run pytest backend/tests/test_voice_sessions.py -v
```

**Success Criteria:**
- ✅ LiveKit server accessible
- ✅ Can create rooms and generate tokens
- ✅ Endpoints working
- ✅ Tests pass

---

### [05-LIVEKIT-VOICE-AGENT.md](./05-LIVEKIT-VOICE-AGENT.md)
**Purpose:** Voice agent worker with STT/TTS and LangChain integration  
**Dependencies:** Sub-Doc 1, 2 (Agents), Sub-Doc 4 (LiveKit Infrastructure)  
**Estimated Time:** 5-7 days  

**What You'll Build:**
- LiveKit voice agent worker process
- Speech-to-Text integration (Deepgram)
- Text-to-Speech integration (Cartesia)
- Function tools for quick queries
- LiveKit-to-LangChain bridge for complex reasoning
- Async logging for non-blocking operations

**Key Files Created:**
- `backend/app/livekit_agents/voice_agent_worker.py` - Main voice agent
- `backend/requirements-agent.txt` - Agent-specific dependencies
- `backend/Dockerfile.agent` - Agent worker Docker image
- Docker Compose configuration for agent workers

**Verification:**
```bash
poetry run pytest backend/tests/test_voice_agent_integration.py -v
```

**Manual Test:**
1. Start voice agent worker
2. Create voice session via API
3. Connect with LiveKit client
4. Speak to agent and verify response

**Success Criteria:**
- ✅ Voice agent worker runs and connects to LiveKit
- ✅ STT/TTS working
- ✅ Function tools callable
- ✅ LangChain delegation works
- ✅ Latency <2 seconds

---

### [06-VOICE-OPTIMIZATION.md](./06-VOICE-OPTIMIZATION.md)
**Purpose:** Production optimization and monitoring  
**Dependencies:** Sub-Doc 5 (Voice Agent)  
**Estimated Time:** 3-4 days  

**What You'll Build:**
- Redis-based context caching for voice sessions
- Prometheus metrics collection
- Error handling and graceful degradation
- Load testing infrastructure
- Monitoring dashboard (Grafana)
- Performance tuning

**Key Files Created:**
- `backend/app/services/context_cache.py` - Redis context caching
- `backend/app/core/metrics.py` - Prometheus metrics
- `backend/app/livekit_agents/error_handling.py` - Error handling
- `backend/tests/load_test_voice.py` - Load testing
- `monitoring/grafana-dashboard.json` - Monitoring dashboard

**Verification:**
```bash
# Run load test
poetry run python backend/tests/load_test_voice.py

# Check metrics
curl http://localhost:8000/metrics | grep voice_response_latency
```

**Success Criteria:**
- ✅ Voice latency <2s (P95)
- ✅ Text latency <3s (P95)
- ✅ Context caching working
- ✅ Metrics collected
- ✅ Error handling robust
- ✅ Load test passed

---

## Implementation Sequence

```
Phase 1 (Completed)
    ↓
Sub-Doc 1: LangChain Foundation (3-5 days)
    ↓
Sub-Doc 2: Specialized Agents (5-7 days)
    ↓
    ├─→ Sub-Doc 3: Text Chat API (2-3 days) ──┐
    │                                          │
    └─→ Sub-Doc 4: LiveKit Infrastructure (2-3 days)
            ↓                                  │
        Sub-Doc 5: LiveKit Voice Agent (5-7 days) ←┘
            ↓
        Sub-Doc 6: Voice Optimization (3-4 days)
```

**Total Estimated Time:** 20-29 days (3-4 weeks)

**Parallel Development Opportunity:**
- Sub-Doc 3 (Text Chat) and Sub-Doc 4 (LiveKit Infrastructure) can be developed simultaneously by different developers after Sub-Doc 2 is complete.

---

## Creating Specs for Each Sub-Doc

For each sub-document, you can create a Kiro spec to track implementation:

```bash
# Example: Create spec for Sub-Doc 1
# In Kiro, say: "Create a spec for LangChain Foundation based on 01-LANGCHAIN-FOUNDATION.md"
```

The spec will include:
- Requirements from the sub-doc
- Implementation tasks
- Verification steps
- Success criteria

---

## Phase 2 Success Criteria

Phase 2 is complete when ALL of the following are verified:

### 1. LangChain Agents Operational
- ✅ All 6 specialized agents implemented
- ✅ Agent orchestrator routes queries correctly
- ✅ Agents can call database tools
- ✅ Multi-provider LLM support working

### 2. Text Chat Working
- ✅ REST API endpoints for chat functional
- ✅ Streaming responses working
- ✅ Conversation history persisted
- ✅ Agent type selection working

### 3. Voice Sessions Working
- ✅ LiveKit rooms can be created
- ✅ Voice agent connects and responds
- ✅ STT (Deepgram) functional
- ✅ TTS (Cartesia) functional
- ✅ LiveKit-to-LangChain bridge working

### 4. Performance Targets Met
- ✅ Voice latency <2 seconds (95th percentile)
- ✅ Text latency <3 seconds (95th percentile)
- ✅ Context caching reduces load time
- ✅ Load test passes (100+ concurrent sessions)

### 5. Integration Tests Pass
- ✅ End-to-end voice session test
- ✅ End-to-end text chat test
- ✅ Agent routing test
- ✅ Context loading test
- ✅ All unit tests pass

### 6. Production Readiness
- ✅ Metrics collection working
- ✅ Error handling in place
- ✅ Monitoring dashboard configured
- ✅ Documentation complete
- ✅ Deployment guide ready

---

## Testing Strategy

### Unit Tests
- Each agent and tool
- Context loading
- Agent orchestration
- LLM integration

### Integration Tests
- Agent routing
- Database operations
- LangChain tool calling
- Voice agent initialization

### End-to-End Tests
- Complete voice session flow
- Complete text chat flow
- Multi-turn conversations
- Agent switching

### Performance Tests
- Load testing (100+ concurrent sessions)
- Latency measurement
- Cache hit rate
- Error rate under load

---

## Common Issues and Solutions

### Issue: LangChain import errors
**Solution:** Ensure all dependencies installed: `poetry install`

### Issue: LiveKit connection fails
**Solution:** 
- Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` in `.env`
- Check LiveKit server is running
- Test connection: `python -c "from app.core.livekit_client import get_livekit_api; print(get_livekit_api())"`

### Issue: Voice agent not responding
**Solution:**
- Check agent worker is running: `docker-compose logs -f livekit_agent`
- Verify Deepgram and Cartesia API keys
- Check room metadata includes `user_id` and `agent_type`

### Issue: High latency (>2s)
**Solution:**
- Enable context caching (Sub-Doc 6)
- Use faster LLM models for classification (Haiku)
- Check database connection pool size
- Verify Redis is accessible

### Issue: Context not loading
**Solution:**
- Verify user profile exists in database
- Check database connection
- Review logs for errors
- Test context loader directly

---

## Development Guidelines

### Code Organization
Follow the structure defined in Phase 1:
```
backend/app/
├── agents/              # LangChain agents (Sub-Doc 1, 2)
│   ├── base.py
│   ├── context.py
│   ├── workout_planner.py
│   ├── diet_planner.py
│   └── ...
├── livekit_agents/      # LiveKit voice agents (Sub-Doc 5)
│   └── voice_agent_worker.py
├── api/v1/endpoints/    # FastAPI endpoints (Sub-Doc 3, 4)
│   ├── chat.py
│   └── voice_sessions.py
├── services/            # Agent orchestrator (Sub-Doc 1)
│   ├── agent_orchestrator.py
│   ├── context_loader.py
│   └── context_cache.py
├── core/                # Shared utilities
│   ├── livekit_client.py
│   └── metrics.py
└── models/              # Database models (already exists)
```

### Testing Conventions
- Unit tests: `test_<module>.py`
- Integration tests: `test_<feature>_integration.py`
- Load tests: `load_test_<feature>.py`
- Use pytest markers: `@pytest.mark.asyncio`, `@pytest.mark.integration`

### Commit Messages
- Format: `[Sub-Doc X] Brief description`
- Examples:
  - `[Sub-Doc 1] Implement base agent class`
  - `[Sub-Doc 2] Add workout planner agent`
  - `[Sub-Doc 5] Integrate Deepgram STT`

---

## Resources

### Documentation
- [Parent TRD](../TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md) - Complete technical specification
- [Backend TRD](../backend_trd.md) - Phase 1 architecture
- [LangChain Docs](https://python.langchain.com) - LangChain documentation
- [LiveKit Docs](https://docs.livekit.io) - LiveKit documentation
- [LiveKit Agents Guide](https://docs.livekit.io/agents/) - LiveKit Agents framework

### API Keys Required
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `GOOGLE_API_KEY` - For LLM
- `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` - For LiveKit
- `DEEPGRAM_API_KEY` - For Speech-to-Text
- `CARTESIA_API_KEY` - For Text-to-Speech

### Tools
- Poetry - Python dependency management
- Docker Compose - Container orchestration
- Pytest - Testing framework
- Prometheus - Metrics collection
- Grafana - Monitoring dashboards

---

## Next Steps After Phase 2

Once Phase 2 is complete and verified, you can proceed to:

1. **Phase 3: Background Jobs & Scheduling**
   - Celery task implementation
   - Notification system
   - Adaptive plan recalculation
   - Scheduled reminders

2. **Phase 4: Client Integration**
   - iOS/Android/Web client development
   - LiveKit client SDK integration
   - Real-time UI updates
   - Push notifications

3. **Phase 5: Production Deployment**
   - Infrastructure setup (AWS/GCP/DigitalOcean)
   - CI/CD pipeline
   - Monitoring and alerting
   - Security hardening

---

## Questions & Support

If you encounter issues or need clarification:

1. **Check the sub-doc** - Each sub-doc has troubleshooting sections
2. **Review the parent TRD** - `TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md`
3. **Check Phase 1 implementation** - For patterns and examples
4. **Consult steering files** - In `.kiro/steering/` for project guidelines
5. **Ask for clarification** - In team discussions or code reviews

---

## Document Status

Track your progress through Phase 2:

- [ ] **Sub-Doc 1:** LangChain Foundation - Not Started
- [ ] **Sub-Doc 2:** Specialized Agents - Not Started
- [ ] **Sub-Doc 3:** Text Chat API - Not Started
- [ ] **Sub-Doc 4:** LiveKit Infrastructure - Not Started
- [ ] **Sub-Doc 5:** LiveKit Voice Agent - Not Started
- [ ] **Sub-Doc 6:** Voice Optimization - Not Started

**Phase 2 Status:** Not Started  
**Last Updated:** February 3, 2026

---

## Summary

This Phase 2 breakdown provides a clear, manageable path to implementing the Hybrid LiveKit + LangChain Agent Architecture. Each sub-doc is:

- **Self-contained** - Can be understood and implemented independently
- **Verified** - Has clear verification steps and success criteria
- **Documented** - Includes code examples and explanations
- **Tested** - Includes test cases and verification commands

Follow the sequence, verify each step, and you'll have a production-ready AI-powered fitness coaching system with both voice and text interactions.

**Good luck with your implementation!** 🚀