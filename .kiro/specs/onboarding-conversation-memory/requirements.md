# Requirements Document

## Introduction

This feature implements conversation memory for onboarding agents by aligning their architecture with the established BaseAgent pattern. Currently, onboarding agents lose conversation context between messages, causing them to ask the same questions repeatedly. This creates a poor user experience during the critical onboarding flow.

The solution standardizes the onboarding agent architecture to match post-onboarding agents, which properly maintain conversation history through an AgentContext object. This ensures consistent behavior across all agent types and enables natural, context-aware conversations during onboarding.

## Glossary

- **BaseAgent**: The abstract base class for post-onboarding agents that includes conversation history management
- **BaseOnboardingAgent**: The abstract base class for onboarding agents that currently lacks conversation history support
- **AgentContext**: Immutable Pydantic model containing user data and conversation history for post-onboarding agents
- **OnboardingAgentContext**: New Pydantic model to be created for onboarding agents with conversation history
- **OnboardingAgentOrchestrator**: Service that routes messages to appropriate onboarding agents and creates agent context
- **ConversationMessage**: Database model storing all user and assistant messages
- **Conversation_History**: List of recent messages in format [{"role": "user"|"assistant", "content": "..."}]

## Requirements

### Requirement 1: Create OnboardingAgentContext Model

**User Story:** As a developer, I want a standardized context model for onboarding agents, so that they have access to conversation history like post-onboarding agents.

#### Acceptance Criteria

1. THE System SHALL define an OnboardingAgentContext class in app/agents/context.py
2. THE OnboardingAgentContext SHALL inherit from Pydantic BaseModel
3. THE OnboardingAgentContext SHALL include a conversation_history field of type List[Dict]
4. THE OnboardingAgentContext SHALL include a user_id field of type str
5. THE OnboardingAgentContext SHALL include an agent_context field of type Dict
6. THE OnboardingAgentContext SHALL be immutable (frozen=True)
7. THE OnboardingAgentContext SHALL include a loaded_at timestamp field

### Requirement 2: Update BaseOnboardingAgent to Use OnboardingAgentContext

**User Story:** As a developer, I want BaseOnboardingAgent to accept OnboardingAgentContext instead of a plain dict, so that all onboarding agents have access to conversation history.

#### Acceptance Criteria

1. THE BaseOnboardingAgent constructor SHALL accept OnboardingAgentContext instead of dict
2. THE BaseOnboardingAgent SHALL store the context as self.context
3. THE BaseOnboardingAgent SHALL provide access to conversation_history through self.context.conversation_history
4. THE BaseOnboardingAgent SHALL provide access to agent_context through self.context.agent_context

### Requirement 3: Add Message Building Helper to BaseOnboardingAgent

**User Story:** As a developer, I want a standardized _build_messages() method in BaseOnboardingAgent, so that all onboarding agents construct LLM messages consistently.

#### Acceptance Criteria

1. THE BaseOnboardingAgent SHALL define a _build_messages(message: str) method
2. THE _build_messages method SHALL return a List of LangChain message objects
3. THE _build_messages method SHALL include the system prompt as the first message
4. THE _build_messages method SHALL include conversation history from self.context.conversation_history
5. THE _build_messages method SHALL limit conversation history to the last 15 messages
6. THE _build_messages method SHALL append the current user message as the last message
7. THE _build_messages method SHALL convert history format from [{"role": "user"|"assistant", "content": "..."}] to LangChain messages

### Requirement 4: Load Conversation History in OnboardingAgentOrchestrator

**User Story:** As a system, I want to load conversation history when creating agent context, so that agents have access to previous messages.

#### Acceptance Criteria

1. WHEN creating an agent, THE OnboardingAgentOrchestrator SHALL query ConversationMessage table for the user's messages
2. THE OnboardingAgentOrchestrator SHALL order messages by created_at ascending
3. THE OnboardingAgentOrchestrator SHALL limit the query to the last 20 messages
4. THE OnboardingAgentOrchestrator SHALL format messages as [{"role": "user"|"assistant", "content": "..."}]
5. THE OnboardingAgentOrchestrator SHALL create an OnboardingAgentContext with the loaded conversation history
6. THE OnboardingAgentOrchestrator SHALL pass the OnboardingAgentContext to the agent constructor

### Requirement 5: Update All Onboarding Agents to Use _build_messages

**User Story:** As a developer, I want all onboarding agents to use the standardized _build_messages() method, so that conversation history is consistently included in LLM calls.

#### Acceptance Criteria

1. THE FitnessAssessmentAgent stream_response method SHALL use self._build_messages(message)
2. THE GoalSettingAgent stream_response method SHALL use self._build_messages(message)
3. THE WorkoutPlanningAgent stream_response method SHALL use self._build_messages(message)
4. THE DietPlanningAgent stream_response method SHALL use self._build_messages(message)
5. THE SchedulingAgent stream_response method SHALL use self._build_messages(message)
6. WHEN using _build_messages, THE agents SHALL remove manual conversation history handling
7. WHEN using _build_messages, THE agents SHALL remove manual prompt construction with ChatPromptTemplate

### Requirement 6: Prevent Token Overflow

**User Story:** As a system, I want to limit conversation history size, so that LLM token limits are not exceeded during onboarding.

#### Acceptance Criteria

1. THE OnboardingAgentOrchestrator SHALL limit conversation history queries to 20 messages maximum
2. THE BaseOnboardingAgent._build_messages SHALL limit included history to 15 messages maximum
3. WHEN conversation history exceeds the limit, THE system SHALL include only the most recent messages
4. THE system SHALL preserve message order (oldest to newest) in the limited history
5. THE system SHALL not truncate individual message content

### Requirement 7: Ensure All Tests Pass

**User Story:** As a developer, I want all existing tests to pass after the changes, so that I know the refactoring did not break existing functionality.

#### Acceptance Criteria

1. WHEN running the test suite, THE system SHALL pass all existing onboarding agent tests
2. WHEN running the test suite, THE system SHALL pass all existing orchestrator tests
3. WHEN running the test suite, THE system SHALL pass all existing context tests
4. THE system SHALL not introduce new test failures
5. THE system SHALL maintain test coverage at current levels or higher
