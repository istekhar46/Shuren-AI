# Phase 2: AI Integration - Overview & Roadmap

## Document Information
**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Planning  
**Parent TRD:** [TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md](../TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md)

---

## Phase 1 Completion Status

### ✅ Completed in Phase 1
- FastAPI project setup with async architecture
- PostgreSQL database with SQLAlchemy 2.0+ async ORM
- Alembic migrations system
- JWT authentication system
- User, Profile, Onboarding models and endpoints
- Meal and Workout basic CRUD operations
- Redis caching infrastructure
- Celery background task framework
- Basic API endpoints (auth, onboarding, profiles, meals, workouts)
- Pydantic schemas for validation
- Testing infrastructure with pytest

### 📍 Current State Verification
To verify Phase 1 completion, check:
```bash
# Database is running and migrated
poetry run alembic current

# Tests pass
poetry run pytest

# API is accessible
curl http://localhost:8000/api/v1/health

# Key endpoints exist
curl http://localhost:8000/docs  # Should show Swagger UI
```

---

## Phase 2 Objectives

Phase 2 implements the **Hybrid LiveKit + LangChain Agent Architecture** for AI-powered fitness coaching with both voice and text interactions.

### Core Goals
1. **LangChain Agent Framework** - Implement 6 specialized AI agents with orchestration
2. **LiveKit Voice Integration** - Enable real-time voice coaching sessions
3. **Text Chat System** - Provide text-based agent interactions via REST API
4. **Agent-Database Bridge** - Connect agents to user context and workout/meal data
5. **Voice Optimization** - Achieve <2s latency for voice interactions
6. **Multi-Provider LLM Support** - Support Anthropic, OpenAI, and Google models

---

## Phase 2 Sub-Documents

Phase 2 is broken into **6 manageable sub-documents**, each representing a logical implementation unit:

### Sub-Doc 1: LangChain Foundation & Base Agent Framework
**File:** `01-LANGCHAIN-FOUNDATION.md`  
**Focus:** Core LangChain setup, base agent class, agent context, and orchestrator skeleton  
**Dependencies:** Phase 1 (database, models)  
**Estimated Effort:** 3-5 days  
**Verification:** Base agent can load user context and respond to simple queries

### Sub-Doc 2: Specialized Agent Implementation
**File:** `02-SPECIALIZED-AGENTS.md`  
**Focus:** Implement 6 specialized agents (Workout, Diet, Supplement, Tracker, Scheduler, General)  
**Dependencies:** Sub-Doc 1  
**Estimated Effort:** 5-7 days  
**Verification:** Each agent can handle domain-specific queries with tools

### Sub-Doc 3: Text Chat API Integration
**File:** `03-TEXT-CHAT-API.md`  
**Focus:** FastAPI endpoints for text chat, streaming responses, conversation history  
**Dependencies:** Sub-Doc 1, Sub-Doc 2  
**Estimated Effort:** 2-3 days  
**Verification:** Text chat works end-to-end via REST API

### Sub-Doc 4: LiveKit Infrastructure Setup
**File:** `04-LIVEKIT-INFRASTRUCTURE.md`  
**Focus:** LiveKit server setup, room management, FastAPI integration for session creation  
**Dependencies:** Phase 1 (auth)  
**Estimated Effort:** 2-3 days  
**Verification:** Can create LiveKit rooms and generate access tokens

### Sub-Doc 5: LiveKit Voice Agent Implementation
**File:** `05-LIVEKIT-VOICE-AGENT.md`  
**Focus:** Voice agent worker with STT/TTS, LiveKit-to-LangChain bridge, function tools  
**Dependencies:** Sub-Doc 1, Sub-Doc 2, Sub-Doc 4  
**Estimated Effort:** 5-7 days  
**Verification:** Voice sessions work end-to-end with agent responses

### Sub-Doc 6: Voice Optimization & Production Readiness
**File:** `06-VOICE-OPTIMIZATION.md`  
**Focus:** Context caching, latency optimization, monitoring, error handling  
**Dependencies:** Sub-Doc 5  
**Estimated Effort:** 3-4 days  
**Verification:** Voice latency <2s, text latency <3s, metrics collected

---

## Implementation Sequence

```
Phase 1 (Completed)
    ↓
Sub-Doc 1: LangChain Foundation
    ↓
Sub-Doc 2: Specialized Agents
    ↓
    ├─→ Sub-Doc 3: Text Chat API (can run in parallel)
    │
    └─→ Sub-Doc 4: LiveKit Infrastructure
            ↓
        Sub-Doc 5: LiveKit Voice Agent
            ↓
        Sub-Doc 6: Voice Optimization
```

### Parallel Development Opportunities
- **Sub-Doc 3** (Text Chat) can be developed in parallel with **Sub-Doc 4** (LiveKit Infrastructure)
- Both depend on Sub-Doc 1 & 2 being complete
- This allows 2 developers to work simultaneously

---

## Success Criteria for Phase 2

Phase 2 is complete when:

1. ✅ **LangChain Agents Operational**
   - All 6 specialized agents implemented
   - Agent orchestrator routes queries correctly
   - Agents can call database tools

2. ✅ **Text Chat Working**
   - REST API endpoints for chat
   - Streaming responses functional
   - Conversation history persisted

3. ✅ **Voice Sessions Working**
   - LiveKit rooms can be created
   - Voice agent connects and responds
   - STT and TTS functional

4. ✅ **Performance Targets Met**
   - Voice latency <2 seconds (95th percentile)
   - Text latency <3 seconds (95th percentile)

5. ✅ **Integration Tests Pass**
   - End-to-end voice session test
   - End-to-end text chat test
   - Agent routing test
   - Context loading test

6. ✅ **Documentation Complete**
   - API documentation updated
   - Deployment guide for LiveKit
   - Environment configuration documented

---

## Development Guidelines

### For Each Sub-Document
1. **Read the sub-doc thoroughly** before starting implementation
2. **Verify dependencies** are complete (check verification steps)
3. **Follow the implementation order** specified in the sub-doc
4. **Run verification steps** after each major component
5. **Update the sub-doc** if you discover issues or improvements

### Testing Strategy
- **Unit tests** for each agent and tool
- **Integration tests** for agent orchestration
- **End-to-end tests** for voice and text paths
- **Performance tests** for latency requirements

### Code Organization
Follow the structure defined in Phase 1:
```
backend/app/
├── agents/              # LangChain agents (Sub-Doc 1, 2)
├── livekit_agents/      # LiveKit voice agents (Sub-Doc 5)
├── api/v1/endpoints/    # FastAPI endpoints (Sub-Doc 3, 4)
├── services/            # Agent orchestrator (Sub-Doc 1)
├── core/                # Shared utilities
└── models/              # Database models (already exists)
```

---

## Risk Mitigation

### Technical Risks
1. **LiveKit Learning Curve** - Mitigated by Sub-Doc 4 focusing only on infrastructure first
2. **Voice Latency** - Mitigated by Sub-Doc 6 dedicated to optimization
3. **LLM API Costs** - Use cheaper models for classification (Haiku), cache aggressively
4. **Agent Complexity** - Start with simple agents in Sub-Doc 2, iterate

### Dependency Risks
1. **External Services** - LiveKit, Anthropic, Deepgram, Cartesia
   - Mitigation: Have fallback providers configured
2. **Database Performance** - Agent context loading
   - Mitigation: Redis caching implemented in Phase 1

---

## Next Steps

1. **Review this overview** with the team
2. **Read Sub-Doc 1** (LangChain Foundation) in detail
3. **Create spec** for Sub-Doc 1 using Kiro's spec workflow
4. **Begin implementation** of Sub-Doc 1
5. **Verify completion** before moving to Sub-Doc 2

---

## Questions & Clarifications

If you encounter issues or need clarification:
1. Check the parent TRD: `TRD_Hybrid_LiveKit_+_LangChain_Agent_Architecture.md`
2. Review Phase 1 implementation for patterns
3. Consult the steering files in `.kiro/steering/`
4. Ask for clarification in team discussions

---

## Document Status

- [ ] Sub-Doc 1: LangChain Foundation - Not Started
- [ ] Sub-Doc 2: Specialized Agents - Not Started
- [ ] Sub-Doc 3: Text Chat API - Not Started
- [ ] Sub-Doc 4: LiveKit Infrastructure - Not Started
- [ ] Sub-Doc 5: LiveKit Voice Agent - Not Started
- [ ] Sub-Doc 6: Voice Optimization - Not Started

**Last Updated:** February 2, 2026
