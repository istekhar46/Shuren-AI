# Implementation Plan: Specialized AI Agents

## Overview

This implementation plan breaks down the development of 6 specialized AI agents into discrete, incremental tasks. Each agent extends BaseAgent and provides domain-specific tools and system prompts. The plan follows a pattern of implementing one agent at a time, testing it, then moving to the next.

The implementation builds on the completed Phase 2 Sub-Doc 1 (LangChain Foundation) which provides BaseAgent, AgentContext, AgentOrchestrator, and TestAgent.

## Tasks

- [x] 1. Implement Workout Planner Agent
  - [x] 1.1 Create WorkoutPlannerAgent class extending BaseAgent
    - Create `backend/app/agents/workout_planner.py`
    - Implement `process_text()` method with LangChain tool calling agent
    - Implement `process_voice()` method for concise responses
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` method with workout-specific prompt
    - _Requirements: 1.5, 1.6, 1.7_
  
  - [x] 1.2 Implement get_current_workout tool
    - Create `@tool` decorated async function
    - Query WorkoutSchedule from database using SQLAlchemy async
    - Return JSON string with workout details
    - Handle database errors gracefully
    - _Requirements: 1.1_
  
  - [x] 1.3 Implement show_exercise_demo tool
    - Create `@tool` decorated async function
    - Query Exercise table for demo_gif_url by exercise name
    - Return URL string or error message
    - Handle missing exercises gracefully
    - _Requirements: 1.2_
  
  - [x] 1.4 Implement log_set_completion tool
    - Create `@tool` decorated async function
    - Insert WorkoutLog entry with exercise, reps, weight
    - Commit to database using async session
    - Return confirmation message
    - _Requirements: 1.3_
  
  - [x] 1.5 Implement suggest_workout_modification tool
    - Create `@tool` decorated async function
    - Use context (fitness_level, energy_level) to generate suggestions
    - Return modification suggestions as JSON string
    - _Requirements: 1.4_
  
  - [x] 1.6 Implement get_tools() method for WorkoutPlannerAgent
    - Return list of all 4 workout tools
    - Ensure tools have access to db_session and context
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 1.7 Write unit tests for WorkoutPlannerAgent
    - Test each tool with valid inputs
    - Test text mode processing
    - Test voice mode processing
    - Test system prompt generation
    - Test error handling in tools
    - _Requirements: 10.1, 10.4, 10.5_
  
  - [ ]* 1.8 Write property test for voice mode conciseness
    - **Property 3: Voice Mode Response Conciseness**
    - **Validates: Requirements 1.6**
    - Generate random fitness contexts
    - Call process_voice() with various queries
    - Verify responses are ≤75 words
    - Run 100 iterations minimum
  
  - [ ]* 1.9 Write property test for text mode formatting
    - **Property 4: Text Mode Markdown Formatting**
    - **Validates: Requirements 1.7**
    - Generate random fitness contexts
    - Call process_text() with various queries
    - Verify responses contain markdown elements
    - Run 100 iterations minimum

- [x] 2. Implement Diet Planner Agent
  - [x] 2.1 Create DietPlannerAgent class extending BaseAgent
    - Create `backend/app/agents/diet_planner.py`
    - Implement `process_text()` method with tool calling
    - Implement `process_voice()` method for concise responses
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` method with nutrition-specific prompt
    - _Requirements: 2.5, 2.6, 2.7_
  
  - [x] 2.2 Implement get_current_meal_plan tool
    - Create `@tool` decorated async function
    - Query MealPlan from database
    - Return JSON string with meal details
    - Handle database errors gracefully
    - _Requirements: 2.1_
  
  - [x] 2.3 Implement suggest_meal_substitution tool
    - Create `@tool` decorated async function
    - Check dietary preferences and restrictions from context
    - Generate alternative meal suggestions
    - Ensure suggestions respect all constraints
    - _Requirements: 2.2, 2.5_
  
  - [x] 2.4 Implement get_recipe_details tool
    - Create `@tool` decorated async function
    - Query Recipe table by dish name
    - Return ingredients and cooking instructions
    - Handle missing recipes gracefully
    - _Requirements: 2.3_
  
  - [x] 2.5 Implement calculate_nutrition tool
    - Create `@tool` decorated async function
    - Query nutritional data for dish
    - Calculate and return macros (protein, carbs, fats) and calories
    - _Requirements: 2.4_
  
  - [x] 2.6 Implement get_tools() method for DietPlannerAgent
    - Return list of all 4 diet tools
    - Ensure tools have access to db_session and context
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 2.7 Write unit tests for DietPlannerAgent
    - Test each tool with valid inputs
    - Test text mode processing
    - Test voice mode processing
    - Test system prompt includes dietary restrictions
    - Test error handling in tools
    - _Requirements: 10.1, 10.4, 10.5_
  
  - [ ]* 2.8 Write property test for dietary constraint satisfaction
    - **Property 7: Dietary Constraint Satisfaction**
    - **Validates: Requirements 2.2, 2.5**
    - Generate random dietary restrictions (vegetarian, allergies, etc.)
    - Call suggest_meal_substitution with various reasons
    - Verify no suggestions violate restrictions
    - Run 100 iterations minimum

- [x] 3. Implement Supplement Guidance Agent
  - [x] 3.1 Create SupplementGuideAgent class extending BaseAgent
    - Create `backend/app/agents/supplement_guide.py`
    - Implement `process_text()` method with tool calling
    - Implement `process_voice()` method with disclaimers
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` with strong non-medical disclaimers
    - _Requirements: 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [x] 3.2 Implement get_supplement_info tool
    - Create `@tool` decorated async function
    - Return general information about supplement
    - Include disclaimer in response
    - _Requirements: 3.1_
  
  - [x] 3.3 Implement check_supplement_interactions tool
    - Create `@tool` decorated async function
    - Check for potential interactions between supplements
    - Return interaction information with disclaimer
    - _Requirements: 3.2_
  
  - [x] 3.4 Implement get_tools() method for SupplementGuideAgent
    - Return list of both supplement tools
    - Ensure tools include disclaimers
    - _Requirements: 3.1, 3.2_
  
  - [ ]* 3.5 Write unit tests for SupplementGuideAgent
    - Test each tool with valid inputs
    - Test text mode processing includes disclaimers
    - Test voice mode processing includes disclaimers
    - Test system prompt emphasizes non-medical guidance
    - _Requirements: 10.1, 10.4_
  
  - [ ]* 3.6 Write property test for disclaimer inclusion
    - **Property 8: Supplement Disclaimer Inclusion**
    - **Validates: Requirements 3.3, 3.4, 3.7**
    - Generate random supplement queries
    - Call process_text() and process_voice()
    - Verify all responses contain disclaimer keywords
    - Run 100 iterations minimum

- [x] 4. Implement Tracking and Adjustment Agent
  - [x] 4.1 Create TrackerAgent class extending BaseAgent
    - Create `backend/app/agents/tracker.py`
    - Implement `process_text()` method with tool calling
    - Implement `process_voice()` method for concise responses
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` with supportive, non-judgmental tone
    - _Requirements: 4.5, 4.6, 4.7_
  
  - [x] 4.2 Implement get_workout_adherence tool
    - Create `@tool` decorated async function
    - Query WorkoutLog for specified number of days
    - Calculate adherence percentage: (completed / scheduled) * 100
    - Return statistics as JSON string
    - _Requirements: 4.1_
  
  - [x] 4.3 Implement get_progress_metrics tool
    - Create `@tool` decorated async function
    - Query user's weight, measurements, and tracked metrics
    - Return progress data as JSON string
    - _Requirements: 4.2_
  
  - [x] 4.4 Implement suggest_plan_adjustment tool
    - Create `@tool` decorated async function
    - Analyze adherence patterns from data
    - Generate adaptive adjustment suggestions
    - Ensure suggestions are supportive, not punitive
    - _Requirements: 4.3, 4.4, 4.5_
  
  - [x] 4.5 Implement get_tools() method for TrackerAgent
    - Return list of all 3 tracking tools
    - Ensure tools have access to db_session and context
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 4.6 Write unit tests for TrackerAgent
    - Test each tool with valid inputs
    - Test adherence calculation accuracy
    - Test text mode processing
    - Test voice mode processing
    - Test error handling in tools
    - _Requirements: 10.1, 10.4, 10.5_
  
  - [ ]* 4.7 Write property test for adherence calculation
    - **Property 9: Adherence Calculation Accuracy**
    - **Validates: Requirements 4.1**
    - Generate random workout logs with known completion rates
    - Call get_workout_adherence tool
    - Verify calculated percentage matches expected value
    - Run 100 iterations minimum

- [x] 5. Implement Scheduling and Reminder Agent
  - [x] 5.1 Create SchedulerAgent class extending BaseAgent
    - Create `backend/app/agents/scheduler.py`
    - Implement `process_text()` method with tool calling
    - Implement `process_voice()` method for concise responses
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` with scheduling focus
    - _Requirements: 5.6, 5.7_
  
  - [x] 5.2 Implement get_upcoming_schedule tool
    - Create `@tool` decorated async function
    - Query upcoming workouts and meals from database
    - Return schedule as JSON string
    - _Requirements: 5.1_
  
  - [x] 5.3 Implement reschedule_workout tool
    - Create `@tool` decorated async function
    - Update workout schedule in database
    - Handle schedule conflicts
    - Return confirmation message
    - _Requirements: 5.2, 5.5_
  
  - [x] 5.4 Implement update_reminder_preferences tool
    - Create `@tool` decorated async function
    - Update user's reminder settings in database
    - Commit changes
    - Return confirmation message
    - _Requirements: 5.3_
  
  - [x] 5.5 Implement get_tools() method for SchedulerAgent
    - Return list of all 3 scheduling tools
    - Ensure tools have access to db_session
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 5.6 Write unit tests for SchedulerAgent
    - Test each tool with valid inputs
    - Test schedule retrieval
    - Test rescheduling updates database
    - Test reminder preference updates
    - Test conflict detection
    - _Requirements: 10.1, 10.4, 10.5_
  
  - [ ]* 5.7 Write property test for schedule conflict detection
    - **Property 10: Schedule Conflict Detection**
    - **Validates: Requirements 5.5**
    - Generate random schedules with known conflicts
    - Call reschedule_workout with conflicting times
    - Verify conflicts are detected and handled
    - Run 100 iterations minimum

- [x] 6. Implement General Assistant Agent
  - [x] 6.1 Create GeneralAssistantAgent class extending BaseAgent
    - Create `backend/app/agents/general_assistant.py`
    - Implement `process_text()` method with tool calling
    - Implement `process_voice()` method for conversational responses
    - Implement `stream_response()` method for streaming
    - Implement `_system_prompt()` with friendly, supportive tone
    - _Requirements: 6.3, 6.5, 6.6, 6.7_
  
  - [x] 6.2 Implement get_user_stats tool
    - Create `@tool` decorated async function
    - Query general user statistics from database
    - Return stats as JSON string
    - _Requirements: 6.4_
  
  - [x] 6.3 Implement provide_motivation tool
    - Create `@tool` decorated async function
    - Use context and progress data to generate motivation
    - Return encouraging message
    - _Requirements: 6.2_
  
  - [x] 6.4 Implement get_tools() method for GeneralAssistantAgent
    - Return list of both general tools
    - Ensure tools have access to db_session and context
    - _Requirements: 6.2, 6.4_
  
  - [x] 6.5 Write unit tests for GeneralAssistantAgent

    - Test each tool with valid inputs
    - Test text mode processing
    - Test voice mode processing
    - Test system prompt has friendly tone
    - _Requirements: 10.1, 10.4_

- [-] 7. Update Agent Orchestrator with Classification
  - [x] 7.1 Update AgentType enum in agent_orchestrator.py
    - Add WORKOUT, DIET, SUPPLEMENT, TRACKER, SCHEDULER, GENERAL
    - Keep TEST for backward compatibility
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [x] 7.2 Implement _classify_query method with LLM classification
    - Add classification system prompt
    - Call classifier LLM (Claude Haiku) with query
    - Parse response to AgentType enum
    - Implement caching for voice mode (first 50 chars)
    - Default to GENERAL on classification failure
    - _Requirements: 7.7, 7.8, 7.9_
  
  - [x] 7.3 Update _create_agent method with all agent types
    - Import all 6 specialized agents
    - Add all agents to agent_map dictionary
    - Keep TestAgent for backward compatibility
    - Raise ValueError for unsupported agent types
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 7.4 Write unit tests for AgentOrchestrator updates
    - Test classification with workout queries
    - Test classification with diet queries
    - Test classification with supplement queries
    - Test classification with tracking queries
    - Test classification with scheduling queries
    - Test classification with general queries
    - Test classification caching in voice mode
    - Test fallback to GENERAL on uncertain classification
    - _Requirements: 10.2, 10.6_

- [x] 8. Checkpoint - Verify all agents work independently
  - Ensure all tests pass for individual agents
  - Verify each agent can process text and voice queries
  - Verify all tools work correctly
  - Ask the user if questions arise

- [ ] 9. Integration Testing
  - [ ]* 9.1 Write integration test for workout query routing
    - Create test that sends workout query to orchestrator
    - Verify routes to WorkoutPlannerAgent
    - Verify response is appropriate
    - _Requirements: 7.1, 10.2_
  
  - [ ]* 9.2 Write integration test for diet query routing
    - Create test that sends diet query to orchestrator
    - Verify routes to DietPlannerAgent
    - Verify response is appropriate
    - _Requirements: 7.2, 10.2_
  
  - [ ]* 9.3 Write integration test for supplement query routing
    - Create test that sends supplement query to orchestrator
    - Verify routes to SupplementGuideAgent
    - Verify response includes disclaimers
    - _Requirements: 7.3, 10.2_
  
  - [ ]* 9.4 Write integration test for tracking query routing
    - Create test that sends tracking query to orchestrator
    - Verify routes to TrackerAgent
    - Verify response is appropriate
    - _Requirements: 7.4, 10.2_
  
  - [ ]* 9.5 Write integration test for scheduling query routing
    - Create test that sends scheduling query to orchestrator
    - Verify routes to SchedulerAgent
    - Verify response is appropriate
    - _Requirements: 7.5, 10.2_
  
  - [ ]* 9.6 Write integration test for general query routing
    - Create test that sends general query to orchestrator
    - Verify routes to GeneralAssistantAgent
    - Verify response is appropriate
    - _Requirements: 7.6, 10.2_
  
  - [ ]* 9.7 Write integration test for all agents responding
    - Create test that queries all 6 agent types
    - Verify each agent returns valid response
    - Verify response format is correct
    - _Requirements: 10.2, 10.3_

- [ ] 10. Property-Based Testing for Cross-Agent Properties
  - [ ]* 10.1 Write property test for agent data retrieval
    - **Property 1: Agent Data Retrieval**
    - **Validates: Requirements 1.1, 2.1, 4.2, 5.1, 6.4**
    - Generate random user contexts
    - Test each agent's data retrieval tools
    - Verify successful database fetches
    - Run 100 iterations minimum
  
  - [ ]* 10.2 Write property test for agent data persistence
    - **Property 2: Agent Data Persistence**
    - **Validates: Requirements 1.3, 5.2, 5.3, 8.2**
    - Generate random data modifications
    - Test each agent's write tools
    - Verify data persists and is retrievable
    - Run 100 iterations minimum
  
  - [ ]* 10.3 Write property test for classification routing accuracy
    - **Property 5: Classification Routing Accuracy**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6**
    - Generate queries with clear domain keywords
    - Test orchestrator classification
    - Verify correct agent routing
    - Run 100 iterations minimum
  
  - [ ]* 10.4 Write property test for classification caching
    - **Property 6: Classification Caching in Voice Mode**
    - **Validates: Requirements 7.8, 9.4**
    - Create orchestrator in voice mode
    - Send same query twice
    - Verify second call uses cache (no LLM call)
    - Run 100 iterations minimum
  
  - [ ]* 10.5 Write property test for database error handling
    - **Property 11: Database Error Handling**
    - **Validates: Requirements 8.4, 8.6**
    - Simulate database errors in tools
    - Verify graceful error handling
    - Verify informative error messages
    - Run 100 iterations minimum
  
  - [ ]* 10.6 Write property test for conversation history truncation
    - **Property 12: Conversation History Truncation**
    - **Validates: Requirements 9.5**
    - Generate long conversation histories
    - Test agents in voice and text modes
    - Verify only last N messages included (5 voice, 10 text)
    - Run 100 iterations minimum
  
  - [ ]* 10.7 Write property test for agent caching in voice mode
    - **Property 13: Agent Caching in Voice Mode**
    - **Validates: Requirements 9.3**
    - Create orchestrator in voice mode
    - Request same agent type twice
    - Verify agent instance is reused
    - Run 100 iterations minimum
  
  - [ ]* 10.8 Write property test for classification fallback
    - **Property 14: Classification Fallback**
    - **Validates: Requirements 7.9**
    - Generate ambiguous queries
    - Test orchestrator classification
    - Verify defaults to GeneralAssistantAgent
    - Run 100 iterations minimum

- [ ] 11. Performance Testing
  - [ ]* 11.1 Write performance test for voice mode latency
    - Test voice mode responses across all agents
    - Measure 95th percentile latency
    - Verify <2 seconds requirement
    - Run 100 queries per agent
    - _Requirements: 9.1_
  
  - [ ]* 11.2 Write performance test for text mode latency
    - Test text mode responses across all agents
    - Measure 95th percentile latency
    - Verify <3 seconds requirement
    - Run 100 queries per agent
    - _Requirements: 9.2_

- [x] 12. Final Checkpoint - Ensure all tests pass
  - Run all unit tests: `poetry run pytest backend/tests/test_*_agent.py -v`
  - Run all integration tests: `poetry run pytest backend/tests/test_agent_routing.py -v`
  - Run all property tests: `poetry run pytest backend/tests/test_agent_properties.py -v`
  - Run performance tests: `poetry run pytest backend/tests/test_agent_performance.py -v`
  - Verify all 6 agents work in both text and voice modes
  - Verify classification routes correctly
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations)
- Unit tests validate specific examples and edge cases
- All agents follow the same implementation pattern for consistency
- Tools must handle database errors gracefully and return JSON responses
- System prompts must be specialized for each agent's domain
- Voice mode responses must be concise (<30 seconds when spoken, ~75 words)
- Text mode responses must include markdown formatting
- Classification uses Claude Haiku for fast, low-cost routing
- Voice mode caches agents and classifications for performance
