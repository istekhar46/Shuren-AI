"""
Property-based tests for state-to-agent mapping consistency.

Validates that the STATE_TO_AGENT_MAP correctly maps all onboarding states (1-9)
to their corresponding specialized agents.
"""

import pytest
from hypothesis import given, strategies as st

from app.services.onboarding_service import STATE_TO_AGENT_MAP
from app.services.agent_orchestrator import AgentType


@pytest.mark.property
class TestStateToAgentMappingProperties:
    """Property-based tests for state-to-agent mapping."""
    
    @given(state=st.integers(min_value=1, max_value=9))
    def test_property_1_state_to_agent_mapping_consistency(self, state: int):
        """
        Property 1: State-to-Agent Mapping Consistency
        
        **Validates: Requirements 2.1.2**
        
        For any valid onboarding state (1-9), verify that:
        1. The state has a corresponding agent mapping
        2. The mapped agent is a valid AgentType
        3. The mapping follows the expected pattern:
           - States 1-3: WORKOUT agent
           - States 4-5: DIET agent
           - States 6-8: SCHEDULER agent
           - State 9: SUPPLEMENT agent
        
        This property ensures that every onboarding state can be routed to
        the correct specialized agent, which is critical for the chat-based
        onboarding flow.
        """
        # Property 1.1: State must have a mapping
        assert state in STATE_TO_AGENT_MAP, \
            f"State {state} is missing from STATE_TO_AGENT_MAP"
        
        # Property 1.2: Mapped value must be a valid AgentType
        agent_type = STATE_TO_AGENT_MAP[state]
        assert isinstance(agent_type, AgentType), \
            f"State {state} maps to {agent_type}, which is not an AgentType"
        
        # Property 1.3: Mapping follows expected pattern
        expected_mappings = {
            1: AgentType.WORKOUT,
            2: AgentType.WORKOUT,
            3: AgentType.WORKOUT,
            4: AgentType.DIET,
            5: AgentType.DIET,
            6: AgentType.SCHEDULER,
            7: AgentType.SCHEDULER,
            8: AgentType.SCHEDULER,
            9: AgentType.SUPPLEMENT,
        }
        
        expected_agent = expected_mappings[state]
        assert agent_type == expected_agent, \
            f"State {state} should map to {expected_agent.value}, but maps to {agent_type.value}"
    
    def test_all_states_have_mappings(self):
        """Test that all 9 onboarding states have agent mappings."""
        expected_states = set(range(1, 10))  # States 1-9
        actual_states = set(STATE_TO_AGENT_MAP.keys())
        
        assert actual_states == expected_states, \
            f"STATE_TO_AGENT_MAP should contain exactly states 1-9. " \
            f"Missing: {expected_states - actual_states}, " \
            f"Extra: {actual_states - expected_states}"
    
    def test_no_invalid_states_in_mapping(self):
        """Test that STATE_TO_AGENT_MAP doesn't contain invalid state numbers."""
        for state in STATE_TO_AGENT_MAP.keys():
            assert 1 <= state <= 9, \
                f"STATE_TO_AGENT_MAP contains invalid state {state}. " \
                f"Valid states are 1-9."
    
    def test_all_mapped_agents_are_valid(self):
        """Test that all agents in the mapping are valid AgentType values."""
        valid_agent_types = {
            AgentType.WORKOUT,
            AgentType.DIET,
            AgentType.SCHEDULER,
            AgentType.SUPPLEMENT,
        }
        
        for state, agent_type in STATE_TO_AGENT_MAP.items():
            assert agent_type in valid_agent_types, \
                f"State {state} maps to {agent_type}, which is not a valid " \
                f"agent type for onboarding. Valid types: {[a.value for a in valid_agent_types]}"
    
    def test_workout_agent_handles_states_1_to_3(self):
        """Test that WORKOUT agent is assigned to states 1-3."""
        workout_states = [1, 2, 3]
        for state in workout_states:
            assert STATE_TO_AGENT_MAP[state] == AgentType.WORKOUT, \
                f"State {state} should be handled by WORKOUT agent"
    
    def test_diet_agent_handles_states_4_to_5(self):
        """Test that DIET agent is assigned to states 4-5."""
        diet_states = [4, 5]
        for state in diet_states:
            assert STATE_TO_AGENT_MAP[state] == AgentType.DIET, \
                f"State {state} should be handled by DIET agent"
    
    def test_scheduler_agent_handles_states_6_to_8(self):
        """Test that SCHEDULER agent is assigned to states 6-8."""
        scheduler_states = [6, 7, 8]
        for state in scheduler_states:
            assert STATE_TO_AGENT_MAP[state] == AgentType.SCHEDULER, \
                f"State {state} should be handled by SCHEDULER agent"
    
    def test_supplement_agent_handles_state_9(self):
        """Test that SUPPLEMENT agent is assigned to state 9."""
        assert STATE_TO_AGENT_MAP[9] == AgentType.SUPPLEMENT, \
            "State 9 should be handled by SUPPLEMENT agent"
    
    @given(
        state=st.integers(min_value=1, max_value=9),
        other_state=st.integers(min_value=1, max_value=9)
    )
    def test_property_mapping_determinism(self, state: int, other_state: int):
        """
        Property: Mapping is deterministic
        
        For any two states, if they are the same, they must map to the same agent.
        If they are different, they may map to the same or different agents
        (depending on the design).
        """
        agent1 = STATE_TO_AGENT_MAP[state]
        agent2 = STATE_TO_AGENT_MAP[other_state]
        
        if state == other_state:
            assert agent1 == agent2, \
                f"Same state {state} should always map to the same agent"
    
    @given(state=st.integers(min_value=1, max_value=9))
    def test_property_agent_type_string_representation(self, state: int):
        """
        Property: Agent type has valid string representation
        
        For any state, the mapped agent type should have a valid string value
        that can be used in API responses.
        """
        agent_type = STATE_TO_AGENT_MAP[state]
        
        # Agent type should have a value attribute
        assert hasattr(agent_type, 'value'), \
            f"AgentType for state {state} should have a 'value' attribute"
        
        # Value should be a non-empty string
        assert isinstance(agent_type.value, str), \
            f"AgentType value for state {state} should be a string"
        assert len(agent_type.value) > 0, \
            f"AgentType value for state {state} should not be empty"
        
        # Value should be one of the expected agent names
        expected_values = {"workout", "diet", "scheduler", "supplement"}
        assert agent_type.value in expected_values, \
            f"AgentType value '{agent_type.value}' for state {state} " \
            f"should be one of {expected_values}"
