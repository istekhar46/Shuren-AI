# Requirements Document

## Introduction

This document specifies the requirements for implementing the LiveKit Voice Agent system for the Shuren fitness application. The Voice Agent enables real-time voice interactions between users and AI fitness coaches through LiveKit's infrastructure, integrating Speech-to-Text (Deepgram), Text-to-Speech (Cartesia), and the existing LangChain agent orchestrator for complex reasoning.

The Voice Agent is part of Phase 2 AI Integration (Sub-Doc 5) and depends on the LangChain Foundation (Sub-Doc 1), Specialized Agents (Sub-Doc 2), and LiveKit Infrastructure (Sub-Doc 4).

## Glossary

- **Voice_Agent**: The LiveKit agent worker process that handles real-time voice interactions with users
- **STT**: Speech-to-Text service (Deepgram) that converts user speech to text
- **TTS**: Text-to-Speech service (Cartesia) that converts agent responses to speech
- **Function_Tool**: A callable function exposed to the LLM for quick data retrieval or actions
- **Agent_Orchestrator**: The LangChain-based service that routes complex queries to specialized agents
- **User_Context**: Pre-loaded user data including profile, workout plans, meal plans, and preferences
- **Log_Worker**: Background async task that persists workout logs to the database
- **Agent_Session**: A LiveKit session connecting STT, TTS, LLM, and the agent logic
- **Room**: A LiveKit room where voice interactions occur
- **Worker**: A long-running process that connects to LiveKit and handles agent sessions

## Requirements

### Requirement 1: Voice Agent SDK Integration

**User Story:** As a developer, I want to integrate the LiveKit Agents SDK with required plugins, so that the voice agent can handle STT, TTS, and LLM operations.

#### Acceptance Criteria

1. THE System SHALL install the latest stable version of livekit-agents with deepgram, openai, and cartesia plugins
2. THE System SHALL install the latest stable versions of langchain, langchain-anthropic, langchain-openai, and langchain-google-genai for multi-provider agent orchestration
3. THE System SHALL install the latest stable version of sqlalchemy with asyncio support for database operations
4. THE System SHALL install the latest stable version of redis with hiredis for caching operations
5. THE System SHALL maintain a separate requirements-agent.txt file for voice agent dependencies

### Requirement 2: Voice Service Configuration

**User Story:** As a system administrator, I want to configure voice service API keys and settings, so that the voice agent can connect to external services.

#### Acceptance Criteria

1. THE System SHALL store Deepgram API key in configuration
2. THE System SHALL store Cartesia API key in configuration
3. THE System SHALL configure voice context cache TTL with default of 3600 seconds
4. THE System SHALL configure maximum response tokens for voice with default of 150 tokens
5. THE System SHALL configure LLM provider selection (openai, anthropic, or google)
6. THE System SHALL store API keys for all supported LLM providers
7. THE System SHALL load all voice configuration from environment variables

### Requirement 3: Voice Agent Worker Implementation

**User Story:** As a fitness coach, I want a voice agent that can handle real-time conversations, so that users can interact naturally with the AI coach.

#### Acceptance Criteria

1. THE Voice_Agent SHALL inherit from the LiveKit Agent base class
2. WHEN initialized, THE Voice_Agent SHALL accept user_id and agent_type parameters
3. THE Voice_Agent SHALL maintain a reference to the Agent_Orchestrator for complex queries
4. THE Voice_Agent SHALL maintain a reference to User_Context for quick data access
5. THE Voice_Agent SHALL provide base instructions appropriate to the agent_type

### Requirement 4: Agent Context Pre-loading

**User Story:** As a user, I want fast voice responses, so that conversations feel natural and responsive.

#### Acceptance Criteria

1. WHEN a Voice_Agent initializes, THE System SHALL load User_Context from the database before connecting to the Room
2. WHEN loading context, THE System SHALL retrieve the user's current workout plan
3. WHEN loading context, THE System SHALL retrieve the user's current meal plan
4. WHEN loading context, THE System SHALL retrieve the user's preferences and constraints
5. WHEN context loading completes, THE System SHALL initialize the Agent_Orchestrator with the loaded context
6. THE System SHALL pre-warm the LLM connection during initialization

### Requirement 5: Quick Data Retrieval Tools

**User Story:** As a user, I want instant answers to simple questions about my workout and meals, so that I don't have to wait for complex processing.

#### Acceptance Criteria

1. THE Voice_Agent SHALL provide a get_todays_workout function tool
2. WHEN get_todays_workout is called, THE System SHALL return workout data from cached User_Context without database queries
3. THE Voice_Agent SHALL provide a get_todays_meals function tool
4. WHEN get_todays_meals is called, THE System SHALL return meal data from cached User_Context without database queries
5. THE System SHALL return tool responses in under 100 milliseconds

### Requirement 6: Workout Logging Tool

**User Story:** As a user, I want to log my workout sets by voice, so that I can track progress without interrupting my workout.

#### Acceptance Criteria

1. THE Voice_Agent SHALL provide a log_workout_set function tool
2. WHEN log_workout_set is called, THE System SHALL accept exercise name, reps, and weight parameters
3. WHEN log_workout_set is called, THE System SHALL queue the log entry for async processing
4. THE System SHALL return a confirmation message immediately without waiting for database write
5. THE System SHALL not block voice interaction while logging to the database

### Requirement 7: Background Workout Logging

**User Story:** As a developer, I want workout logs to be persisted asynchronously, so that voice interactions remain responsive.

#### Acceptance Criteria

1. THE Voice_Agent SHALL maintain an async queue for workout log entries
2. WHEN the Voice_Agent starts, THE System SHALL start a background Log_Worker task
3. WHEN a log entry is queued, THE Log_Worker SHALL retrieve it from the queue
4. WHEN the Log_Worker processes an entry, THE System SHALL write it to the database
5. WHEN the Voice_Agent shuts down, THE System SHALL cancel the Log_Worker task gracefully
6. IF the Log_Worker encounters an error, THE System SHALL log the error and continue processing

### Requirement 8: Specialist Agent Delegation

**User Story:** As a user, I want complex questions to be handled by specialized agents, so that I receive expert guidance.

#### Acceptance Criteria

1. THE Voice_Agent SHALL provide an ask_specialist_agent function tool
2. WHEN ask_specialist_agent is called, THE System SHALL accept query and specialist parameters
3. WHEN ask_specialist_agent is called, THE System SHALL route the query to the Agent_Orchestrator
4. THE System SHALL support routing to workout, diet, and supplement specialists
5. WHEN the Agent_Orchestrator returns a response, THE System SHALL return the response content to the user
6. IF the Agent_Orchestrator fails, THE System SHALL return a friendly error message asking the user to rephrase

### Requirement 9: Voice Agent Session Management

**User Story:** As a user, I want to start voice coaching sessions, so that I can receive real-time guidance.

#### Acceptance Criteria

1. WHEN a Room connection is requested, THE System SHALL extract user_id from room metadata
2. WHEN a Room connection is requested, THE System SHALL extract agent_type from room metadata
3. IF user_id is missing from metadata, THE System SHALL log an error and abort connection
4. WHEN connecting to a Room, THE System SHALL create a Voice_Agent instance
5. WHEN connecting to a Room, THE System SHALL pre-load the Agent_Orchestrator before connecting
6. WHEN connecting to a Room, THE System SHALL start the Log_Worker before connecting
7. WHEN the Agent_Session starts, THE System SHALL generate an initial greeting appropriate to the agent_type

### Requirement 10: Speech-to-Text Configuration

**User Story:** As a user, I want my speech to be accurately transcribed, so that the agent understands my questions.

#### Acceptance Criteria

1. THE System SHALL configure Deepgram STT with the nova-2-general model
2. THE System SHALL configure Deepgram STT for English (en-US) language
3. THE System SHALL use Deepgram STT for all voice input transcription

### Requirement 11: Text-to-Speech Configuration

**User Story:** As a user, I want natural-sounding voice responses, so that interactions feel human-like.

#### Acceptance Criteria

1. THE System SHALL configure Cartesia TTS with the sonic-english model
2. THE System SHALL configure Cartesia TTS with a fitness-coach voice
3. THE System SHALL configure Cartesia TTS with 24000 Hz sample rate
4. THE System SHALL configure Cartesia TTS with 1.1x speed for efficiency
5. THE System SHALL use Cartesia TTS for all voice output generation

### Requirement 12: LLM Configuration for Function Calling

**User Story:** As a developer, I want the LLM to intelligently call function tools, so that the agent can access data and perform actions.

#### Acceptance Criteria

1. THE System SHALL support configurable LLM provider (OpenAI, Anthropic, or Google)
2. THE System SHALL configure OpenAI GPT-4o when OpenAI provider is selected
3. THE System SHALL configure Anthropic Claude when Anthropic provider is selected
4. THE System SHALL configure Google Gemini when Google provider is selected
5. THE System SHALL configure the LLM with 0.7 temperature for balanced creativity
6. THE System SHALL enable the LLM to call all registered function tools
7. WHEN the LLM calls a function tool, THE System SHALL execute the tool and return results to the LLM

### Requirement 13: Agent Worker Process

**User Story:** As a system administrator, I want a worker process that handles multiple voice sessions, so that the system can scale.

#### Acceptance Criteria

1. THE System SHALL provide a main entrypoint function for the agent worker
2. WHEN the worker starts, THE System SHALL configure worker options with the entrypoint function
3. THE System SHALL configure the worker as a ROOM type worker
4. THE System SHALL support configurable number of idle workers
5. WHEN the worker runs, THE System SHALL listen for room connection requests
6. WHEN a room connection is requested, THE System SHALL invoke the entrypoint function

### Requirement 14: Agent Cleanup

**User Story:** As a developer, I want proper resource cleanup, so that the system doesn't leak resources.

#### Acceptance Criteria

1. WHEN an Agent_Session completes, THE System SHALL wait for session completion
2. WHEN an Agent_Session completes, THE System SHALL call the Voice_Agent cleanup method
3. WHEN cleanup is called, THE System SHALL cancel the Log_Worker task
4. WHEN cleanup is called, THE System SHALL wait for the Log_Worker to finish cancellation
5. WHEN cleanup completes, THE System SHALL log the session end

### Requirement 15: Voice Agent Containerization

**User Story:** As a DevOps engineer, I want the voice agent to run in a container, so that it can be deployed consistently.

#### Acceptance Criteria

1. THE System SHALL provide a Dockerfile.agent for building the voice agent container
2. THE Dockerfile SHALL use Python 3.11-slim as the base image
3. THE Dockerfile SHALL install gcc for compiling dependencies
4. THE Dockerfile SHALL install dependencies from requirements-agent.txt
5. THE Dockerfile SHALL copy the application code
6. THE Dockerfile SHALL run the voice agent worker as the main process

### Requirement 16: Voice Agent Service Orchestration

**User Story:** As a DevOps engineer, I want to deploy multiple voice agent workers, so that the system can handle concurrent sessions.

#### Acceptance Criteria

1. THE System SHALL define a livekit_agent service in docker-compose.yml
2. THE livekit_agent service SHALL use Dockerfile.agent for building
3. THE livekit_agent service SHALL configure LiveKit connection environment variables
4. THE livekit_agent service SHALL configure database connection environment variables
5. THE livekit_agent service SHALL configure Redis connection environment variables
6. THE livekit_agent service SHALL configure LLM provider environment variables
7. THE livekit_agent service SHALL configure voice service API keys
8. THE livekit_agent service SHALL depend on postgres and redis services
9. THE livekit_agent service SHALL support running multiple replicas

### Requirement 17: Voice Agent Testing

**User Story:** As a developer, I want comprehensive tests for the voice agent, so that I can verify functionality.

#### Acceptance Criteria

1. THE System SHALL provide integration tests for voice agent initialization
2. THE System SHALL provide tests for the get_todays_workout tool
3. THE System SHALL provide tests for the log_workout_set tool
4. THE System SHALL provide tests for the ask_specialist_agent tool
5. WHEN testing agent initialization, THE System SHALL verify the Agent_Orchestrator is initialized
6. WHEN testing agent initialization, THE System SHALL verify User_Context is loaded
7. WHEN testing workout tool, THE System SHALL verify cached data is returned
8. WHEN testing logging tool, THE System SHALL verify data is queued
9. WHEN testing specialist tool, THE System SHALL verify delegation to Agent_Orchestrator works

### Requirement 18: Voice Response Latency

**User Story:** As a user, I want fast voice responses, so that conversations feel natural.

#### Acceptance Criteria

1. THE System SHALL achieve voice response latency under 2 seconds at 95th percentile
2. WHEN using function tools, THE System SHALL respond in under 500 milliseconds
3. WHEN delegating to specialists, THE System SHALL respond in under 2 seconds
4. THE System SHALL measure and log response latency for monitoring

### Requirement 19: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can diagnose issues.

#### Acceptance Criteria

1. WHEN the Voice_Agent encounters an error, THE System SHALL log the error with context
2. WHEN room metadata is invalid, THE System SHALL log an error and abort gracefully
3. WHEN the Agent_Orchestrator fails, THE System SHALL return a user-friendly error message
4. WHEN the Log_Worker encounters an error, THE System SHALL log the error and continue processing
5. THE System SHALL log all agent session starts and ends
6. THE System SHALL log all function tool invocations

### Requirement 20: Voice Agent Instructions

**User Story:** As a user, I want the voice agent to understand its role, so that it provides appropriate guidance.

#### Acceptance Criteria

1. THE Voice_Agent SHALL provide base instructions that describe its role as a fitness coach
2. THE Voice_Agent SHALL tailor instructions based on the agent_type
3. THE Voice_Agent SHALL instruct the LLM to answer quick questions about workouts and meals
4. THE Voice_Agent SHALL instruct the LLM to log workout progress
5. THE Voice_Agent SHALL instruct the LLM to provide motivation and encouragement
6. THE Voice_Agent SHALL instruct the LLM to use ask_specialist_agent for complex queries
7. THE Voice_Agent SHALL instruct the LLM to keep responses under 30 seconds when spoken
8. THE Voice_Agent SHALL instruct the LLM to maintain a conversational tone
