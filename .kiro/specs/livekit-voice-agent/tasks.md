# Implementation Plan: LiveKit Voice Agent

## Overview

This implementation plan breaks down the LiveKit Voice Agent feature into discrete, incremental coding tasks. Each task builds on previous work and includes specific requirements references. The implementation follows the hybrid architecture where quick queries use function tools with cached data, while complex queries delegate to the LangChain orchestrator.

The voice agent will achieve <2 second latency by pre-loading user context and orchestrator before connecting to LiveKit rooms, using cached data for quick queries, and processing workout logs asynchronously.

## Tasks

- [x] 1. Install LiveKit Agents SDK and dependencies
  - Add livekit-agents with deepgram, openai, and cartesia plugins using Poetry
  - Add langchain-openai and langchain-google-genai for multi-provider support
  - Verify all dependencies resolve correctly
  - _Requirements: 1.1, 1.2_

- [x] 2. Update configuration for voice services
  - [x] 2.1 Add voice service configuration to app/core/config.py
    - Add DEEPGRAM_API_KEY, CARTESIA_API_KEY settings
    - Add VOICE_CONTEXT_CACHE_TTL (default 3600)
    - Add VOICE_MAX_RESPONSE_TOKENS (default 150)
    - Add VOICE_LLM_PROVIDER setting (openai, anthropic, google)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [x] 2.2 Update .env.example with voice service variables
    - Add DEEPGRAM_API_KEY placeholder
    - Add CARTESIA_API_KEY placeholder
    - Add VOICE_LLM_PROVIDER with default value
    - Add VOICE_CONTEXT_CACHE_TTL and VOICE_MAX_RESPONSE_TOKENS
    - _Requirements: 2.6, 2.7_

- [x] 3. Create WorkoutLog database model
  - [x] 3.1 Create app/models/workout_log.py
    - Define WorkoutLog model with id, user_id, exercise, reps, weight_kg, logged_at, created_at
    - Add indexes on user_id and logged_at
    - Add relationship to User model
    - _Requirements: 7.4_
  
  - [x] 3.2 Create database migration for workout_logs table
    - Generate Alembic migration: `poetry run alembic revision --autogenerate -m "add workout_logs table"`
    - Review and apply migration: `poetry run alembic upgrade head`
    - _Requirements: 7.4_

- [x] 4. Implement FitnessVoiceAgent class
  - [x] 4.1 Create app/livekit_agents/ directory and __init__.py
    - Create directory structure
    - Add __init__.py with module docstring
    - _Requirements: 3.1_
  
  - [x] 4.2 Create app/livekit_agents/voice_agent_worker.py with FitnessVoiceAgent class
    - Import LiveKit agents SDK and required dependencies
    - Define FitnessVoiceAgent class inheriting from Agent
    - Implement __init__ with user_id and agent_type parameters
    - Initialize orchestrator and user_context attributes
    - Initialize _log_queue and _log_worker_task attributes
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 4.3 Implement initialize_orchestrator method
    - Load user context using load_agent_context
    - Initialize AgentOrchestrator with db_session and mode="voice"
    - Call orchestrator.warm_up() to pre-warm LLM connection
    - Log initialization completion
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 4.4 Implement _get_base_instructions method
    - Accept agent_type parameter
    - Return instructions tailored to agent_type
    - Include role description, capabilities, and behavioral guidelines
    - Instruct to keep responses under 30 seconds when spoken
    - Instruct to use ask_specialist_agent for complex queries
    - _Requirements: 3.5, 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8_

- [x] 5. Implement function tools
  - [x] 5.1 Implement get_todays_workout function tool
    - Decorate with @function_tool()
    - Accept RunContext parameter
    - Return workout data from self.user_context.current_workout_plan
    - Format as readable string with workout name and exercises
    - Handle case where context not loaded
    - _Requirements: 5.1, 5.2_
  
  - [x] 5.2 Implement get_todays_meals function tool
    - Decorate with @function_tool()
    - Accept RunContext parameter
    - Return meal data from self.user_context.current_meal_plan
    - Format as JSON string
    - Handle case where context not loaded
    - _Requirements: 5.3, 5.4_
  
  - [x] 5.3 Implement log_workout_set function tool
    - Decorate with @function_tool()
    - Accept RunContext, exercise, reps, weight parameters
    - Create log entry dict with timestamp
    - Queue entry to self._log_queue
    - Return immediate confirmation message
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 5.4 Implement ask_specialist_agent function tool
    - Decorate with @function_tool()
    - Accept RunContext, query, specialist parameters
    - Validate specialist is one of: workout, diet, supplement
    - Call self.orchestrator.route_query with voice_mode=True
    - Return response.content
    - Handle orchestrator errors with friendly message
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 6. Implement background log worker
  - [x] 6.1 Implement start_log_worker method
    - Create asyncio task for _log_worker
    - Store task in self._log_worker_task
    - _Requirements: 7.2_
  
  - [x] 6.2 Implement _log_worker method
    - Create infinite loop with try/except
    - Await log entry from self._log_queue
    - Create async database session
    - Create WorkoutLog instance from entry
    - Add to session and commit
    - Call task_done() on queue
    - Handle asyncio.CancelledError for graceful shutdown
    - Log errors and continue processing on exception
    - _Requirements: 7.3, 7.4, 7.6_
  
  - [x] 6.3 Implement cleanup method
    - Cancel self._log_worker_task if exists
    - Await task with CancelledError handling
    - _Requirements: 14.3, 14.4_

- [x] 7. Implement agent session configuration
  - [x] 7.1 Create _get_configured_llm helper function
    - Check settings.VOICE_LLM_PROVIDER
    - Return openai.LLM with gpt-4o if provider is "openai"
    - Return configured LLM for anthropic provider (may need custom integration)
    - Return configured LLM for google provider (may need custom integration)
    - Raise ValueError for unsupported providers
    - Set temperature to 0.7 for all providers
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [x] 7.2 Configure STT with Deepgram in entrypoint
    - Create deepgram.STT instance
    - Set model to "nova-2-general"
    - Set language to "en-US"
    - _Requirements: 10.1, 10.2_
  
  - [x] 7.3 Configure TTS with Cartesia in entrypoint
    - Create cartesia.TTS instance
    - Set model to "sonic-english"
    - Set voice_id to "fitness-coach-male"
    - Set sample_rate to 24000
    - Set speed to 1.1
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 8. Implement agent worker entrypoint
  - [x] 8.1 Implement entrypoint function
    - Accept JobContext parameter
    - Extract metadata from ctx.room.metadata
    - Parse user_id and agent_type from metadata
    - Validate user_id exists, log error and return if missing
    - Log agent session start
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 8.2 Initialize agent and pre-load context in entrypoint
    - Create FitnessVoiceAgent instance
    - Call agent.initialize_orchestrator() before connecting
    - Call agent.start_log_worker() before connecting
    - _Requirements: 9.4, 9.5, 9.6_
  
  - [x] 8.3 Connect to room and start session in entrypoint
    - Call await ctx.connect()
    - Create AgentSession with STT, TTS, and LLM
    - Call await session.start(room=ctx.room, agent=agent)
    - Generate initial greeting with session.generate_reply
    - Await session.wait_for_completion()
    - _Requirements: 9.7_
  
  - [x] 8.4 Implement cleanup in entrypoint
    - Call agent.cleanup() after session completes
    - Log session end
    - _Requirements: 14.1, 14.2, 14.5_

- [x] 9. Implement main worker process
  - [x] 9.1 Add main block to voice_agent_worker.py
    - Check if __name__ == "__main__"
    - Call agents.cli.run_app with WorkerOptions
    - Set entrypoint_fnc to entrypoint function
    - Set num_idle_workers from settings
    - Set worker_type to agents.WorkerType.ROOM
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6_

- [x] 10. Create Dockerfile for voice agent
  - [x] 10.1 Create backend/Dockerfile.agent
    - Use python:3.11-slim as base image
    - Install gcc for compiling dependencies
    - Copy and install from requirements-agent.txt (or use Poetry)
    - Copy application code
    - Set CMD to run voice_agent_worker.py
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [x] 11. Update Docker Compose configuration
  - [x] 11.1 Add livekit_agent service to docker-compose.yml
    - Set build context to ./backend with Dockerfile.agent
    - Add LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET env vars
    - Add DATABASE_URL and REDIS_URL env vars
    - Add LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY env vars
    - Add DEEPGRAM_API_KEY and CARTESIA_API_KEY env vars
    - Set depends_on to postgres and redis
    - Set replicas to 2 in deploy section
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9_

- [x] 12. Checkpoint - Verify voice agent worker runs
  - Start voice agent worker locally: `poetry run python backend/app/livekit_agents/voice_agent_worker.py`
  - Verify worker connects to LiveKit
  - Verify no startup errors
  - Stop worker gracefully
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Write integration tests
  - [x]* 13.1 Create backend/tests/test_voice_agent_integration.py
    - Import required test fixtures and dependencies
    - _Requirements: 17.1_
  
  - [x]* 13.2 Write test for voice agent initialization
    - Create FitnessVoiceAgent with test user
    - Call initialize_orchestrator()
    - Assert orchestrator is not None
    - Assert user_context is not None
    - Assert user_context.user_id matches test user
    - _Requirements: 17.5, 17.6_
  
  - [x]* 13.3 Write test for get_todays_workout tool
    - Create FitnessVoiceAgent with test user
    - Call initialize_orchestrator()
    - Create mock RunContext
    - Call get_todays_workout(mock_context)
    - Assert result is string
    - Assert result length > 0
    - _Requirements: 17.2, 17.7_
  
  - [x]* 13.4 Write test for log_workout_set tool
    - Create FitnessVoiceAgent with test user
    - Call start_log_worker()
    - Create mock RunContext
    - Call log_workout_set with test data
    - Assert result contains "Logged"
    - Assert result contains exercise name
    - Call cleanup()
    - _Requirements: 17.3, 17.8_
  
  - [x]* 13.5 Write test for ask_specialist_agent tool
    - Create FitnessVoiceAgent with test user
    - Call initialize_orchestrator()
    - Create mock RunContext
    - Call ask_specialist_agent with test query and specialist
    - Assert result is string
    - Assert result length > 0
    - _Requirements: 17.4, 17.9_

- [ ]* 14. Write property-based tests
  - [ ]* 14.1 Create backend/tests/test_voice_agent_properties.py
    - Import hypothesis and required dependencies
    - Configure hypothesis to run 100 iterations per test
    - _Requirements: Property testing framework_
  
  - [ ]* 14.2 Write property test for context loading completeness (Property 1)
    - **Property 1: Context Loading Completeness**
    - **Validates: Requirements 4.2, 4.3, 4.4**
    - Use @given with user_id strategy
    - Create agent and initialize orchestrator
    - Assert context includes workout_plan, meal_plan, and preferences
  
  - [ ]* 14.3 Write property test for quick tools using cached data (Property 2)
    - **Property 2: Quick Tools Use Cached Data**
    - **Validates: Requirements 5.2, 5.4**
    - Use @given with user context strategy
    - Call get_todays_workout and get_todays_meals
    - Assert no database queries made (mock db session)
  
  - [ ]* 14.4 Write property test for workout logging queues immediately (Property 3)
    - **Property 3: Workout Logging Queues Immediately**
    - **Validates: Requirements 6.3**
    - Use @given with exercise, reps, weight strategies
    - Call log_workout_set
    - Assert entry added to queue
  
  - [ ]* 14.5 Write property test for specialist delegation flow (Property 7)
    - **Property 7: Specialist Delegation Flow**
    - **Validates: Requirements 8.3, 8.5**
    - Use @given with query and specialist strategies
    - Call ask_specialist_agent
    - Assert query routed to orchestrator
    - Assert response returned
  
  - [ ]* 14.6 Write property test for all specialist types supported (Property 8)
    - **Property 8: All Specialist Types Supported**
    - **Validates: Requirements 8.4**
    - Use @given with specialist type strategy (workout, diet, supplement)
    - Call ask_specialist_agent for each type
    - Assert successful routing for all types
  
  - [ ]* 14.7 Write property test for room metadata extraction (Property 10)
    - **Property 10: Room Metadata Extraction**
    - **Validates: Requirements 9.1, 9.2**
    - Use @given with user_id and agent_type strategies
    - Create room metadata dict
    - Extract user_id and agent_type
    - Assert both extracted correctly
  
  - [ ]* 14.8 Write property test for instructions vary by agent type (Property 14)
    - **Property 14: Instructions Vary By Agent Type**
    - **Validates: Requirements 3.5, 20.2**
    - Use @given with agent_type strategy
    - Create agent with agent_type
    - Get base instructions
    - Assert instructions mention agent_type
    - Assert instructions are non-empty

- [ ] 15. Write unit tests for error handling
  - [ ]* 15.1 Create backend/tests/test_voice_agent_errors.py
    - Import required test fixtures and dependencies
    - _Requirements: 19.1, 19.2, 19.3, 19.4_
  
  - [ ]* 15.2 Write test for missing user_id in metadata
    - Create room metadata without user_id
    - Call entrypoint with mock context
    - Assert error logged
    - Assert connection aborted
    - _Requirements: 9.3, 19.2_
  
  - [ ]* 15.3 Write test for orchestrator failure handling
    - Mock orchestrator to raise exception
    - Call ask_specialist_agent
    - Assert friendly error message returned
    - Assert error logged
    - _Requirements: 8.6, 19.3_
  
  - [ ]* 15.4 Write test for log worker error handling
    - Mock database to raise exception
    - Queue log entry
    - Assert error logged
    - Assert worker continues processing
    - _Requirements: 7.6, 19.4_

- [ ] 16. Final checkpoint - End-to-end verification
  - Build Docker image: `docker build -f backend/Dockerfile.agent -t voice-agent .`
  - Start services: `docker-compose up -d livekit_agent`
  - Check logs: `docker-compose logs -f livekit_agent`
  - Verify worker connects to LiveKit
  - Verify no errors in logs
  - Run all tests: `poetry run pytest backend/tests/test_voice_agent_*.py -v`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Use `poetry add` for all dependency installations (never `pip install`)
- Use `poetry run` prefix for all Python commands
- The voice agent runs as a separate worker process from the main FastAPI application
- Pre-loading context and orchestrator before connecting to rooms is critical for <2s latency
- Function tools use cached data to avoid database queries during voice interactions
- Background log worker ensures non-blocking workout logging
