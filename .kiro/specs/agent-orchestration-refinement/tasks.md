# Implementation Plan: Agent Orchestration Refinement

## Overview

This implementation plan breaks down the agent orchestration refinement into discrete, incremental tasks. Each task builds on previous work and includes testing to validate functionality early.

## Tasks

- [x] 1. Implement enhanced access control method
  - [x] 1.1 Create _enforce_access_control() method
    - Add method to AgentOrchestrator class
    - Implement onboarding mode validation logic
    - Implement post-onboarding mode validation logic
    - Add comprehensive error messages
    - Add logging for access violations
    - _Requirements: 3.1, 3.2_
  
  - [x] 1.2 Write unit tests for access control
    - Test onboarding mode allows specialized agents
    - Test onboarding mode blocks general agent
    - Test onboarding mode blocks tracker agent
    - Test post-onboarding allows general agent
    - Test post-onboarding blocks specialized agents
    - Test onboarding complete rejects onboarding mode
    - Test onboarding incomplete rejects normal mode
    - Test missing onboarding state raises error
    - _Requirements: 3.1, 5.1_
  
  - [x] 1.3 Write property test for access control consistency
    - **Property: Access Control Consistency**
    - **Validates: Requirements 2.1.1-2.1.6, 2.2.1-2.2.3**
    - For any combination of onboarding_complete, onboarding_mode, and agent_type, verify consistent access control decisions

- [x] 2. Enhance classification method
  - [x] 2.1 Add onboarding_mode parameter to _classify_query()
    - Update method signature
    - Add parameter to docstring
    - _Requirements: 3.5_
  
  - [x] 2.2 Implement onboarding-specific classification prompt
    - Create prompt for onboarding mode (specialized agents only)
    - Update cache key to include onboarding_mode
    - Update default fallback based on mode
    - _Requirements: 3.5.1_
  
  - [x] 2.3 Update post-onboarding classification
    - Keep existing prompt for post-onboarding
    - Log original classification for analytics
    - _Requirements: 3.5.2_
  
  - [x] 2.4 Write unit tests for classification
    - Test classification during onboarding returns specialized agents
    - Test classification post-onboarding returns any agent type
    - Test cache key separation by onboarding mode
    - Test default to WORKOUT during onboarding
    - Test default to GENERAL post-onboarding
    - _Requirements: 3.5, 5.1_
  
  - [x] 2.5 Write property test for classification consistency
    - **Property: Classification Mode Consistency**
    - **Validates: Requirements 3.5**
    - For any query and onboarding_mode, verify classification returns appropriate agent types

- [x] 3. Implement enhanced logging
  - [x] 3.1 Create _log_routing_decision() method
    - Add method to AgentOrchestrator class
    - Include all required fields (user_id, agent_type, onboarding_mode, etc.)
    - Add performance metrics (routing_time_ms)
    - _Requirements: 3.3, 2.3.1-2.3.5_
  
  - [x] 3.2 Add access violation logging
    - Log warnings for all access control violations
    - Include violation reason and context
    - _Requirements: 3.2, 2.3.2_
  
  - [x] 3.3 Add performance logging
    - Log classification time
    - Log agent creation time
    - Log total routing time
    - _Requirements: 3.3, 2.3.4_
  
  - [x] 3.4 Write unit tests for logging
    - Test routing decision logged with all fields
    - Test access violation logged as warning
    - Test performance metrics included in logs
    - _Requirements: 3.3, 5.1_

- [x] 4. Update route_query() method
  - [x] 4.1 Add call to _enforce_access_control()
    - Call after loading user and onboarding state
    - Pass all required parameters
    - Handle ValueError exceptions
    - _Requirements: 3.1, 3.4_
  
  - [x] 4.2 Pass onboarding_mode to _classify_query()
    - Update method call
    - Pass onboarding_mode parameter
    - _Requirements: 3.5_
  
  - [x] 4.3 Add force GENERAL agent logic
    - After classification, check if post-onboarding
    - Force agent_type = GENERAL if not TEST agent
    - Log the override for analytics
    - _Requirements: 3.5.2_
  
  - [x] 4.4 Add call to _log_routing_decision()
    - Call at end of method
    - Pass all required parameters
    - Include performance timing
    - _Requirements: 3.3_
  
  - [x] 4.5 Add performance timing
    - Record start time at method entry
    - Calculate routing time at end
    - Pass to logging method
    - _Requirements: 3.3, 4.1_
  
  - [x] 4.6 Write unit tests for route_query updates
    - Test access control is enforced
    - Test classification receives onboarding_mode
    - Test GENERAL agent forced post-onboarding
    - Test routing decision is logged
    - Test performance timing is recorded
    - _Requirements: 3.4, 5.1_

- [x] 5. Update context loader integration
  - [x] 5.1 Pass onboarding_mode to load_agent_context()
    - Update method call in route_query()
    - Ensure context loader handles parameter
    - _Requirements: 3.4_
  
  - [x] 5.2 Verify context loader behavior
    - Check if context loader needs updates
    - Test partial context loading during onboarding
    - Test full context loading post-onboarding
    - _Requirements: 3.4_

- [x] 6. Checkpoint - Test core functionality
  - Run all unit tests: `poetry run pytest tests/test_agent_orchestrator_refinement.py`
  - Verify all access control scenarios work
  - Verify classification works with onboarding_mode
  - Verify logging includes all required fields
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Integration testing
  - [ ] 7.1 Write integration test for onboarding flow
    - Test complete onboarding flow with agent routing
    - Verify specialized agents are accessible
    - Verify general agent is blocked
    - Verify state transitions work correctly
    - _Requirements: 2.1, 5.2_
  
  - [ ] 7.2 Write integration test for post-onboarding flow
    - Test post-onboarding flow with general agent
    - Verify specialized agents are blocked
    - Verify general agent has full context
    - _Requirements: 2.2, 5.2_
  
  - [ ] 7.3 Write integration test for access violations
    - Test all access control violation scenarios
    - Verify error messages are correct
    - Verify logging is correct
    - _Requirements: 2.3, 5.2_
  
  - [ ] 7.4 Write integration test with real database
    - Test with real user and onboarding state
    - Test context loading
    - Test agent creation
    - _Requirements: 5.2_

- [ ] 8. Property-based testing
  - [ ] 8.1 Write property test for access control
    - **Property: Access Control Enforcement**
    - **Validates: Requirements 2.1, 2.2**
    - For any user state and agent request, verify access control is enforced correctly
  
  - [ ] 8.2 Write property test for error messages
    - **Property: Error Message Completeness**
    - **Validates: Requirements 2.4**
    - For any access violation, verify error message includes context and corrective action
  
  - [ ] 8.3 Write property test for logging
    - **Property: Logging Completeness**
    - **Validates: Requirements 2.3**
    - For any routing decision, verify all required fields are logged

- [ ] 9. Performance testing
  - [ ] 9.1 Benchmark access control check
    - Measure time for _enforce_access_control()
    - Verify < 5ms target
    - _Requirements: 4.1_
  
  - [ ] 9.2 Benchmark classification
    - Measure time for _classify_query()
    - Verify < 500ms target (with caching)
    - _Requirements: 4.1_
  
  - [ ] 9.3 Benchmark total routing
    - Measure time for route_query()
    - Verify < 2s voice, < 3s text targets
    - _Requirements: 4.1_
  
  - [ ] 9.4 Load testing
    - Test with 100 concurrent requests
    - Verify performance under load
    - Check for memory leaks
    - _Requirements: 4.1_

- [ ] 10. Documentation updates
  - [ ] 10.1 Update AgentOrchestrator docstrings
    - Update class docstring
    - Update route_query() docstring
    - Add docstrings for new methods
    - _Requirements: All_
  
  - [ ] 10.2 Update API documentation
    - Document access control rules
    - Document error messages
    - Document logging format
    - _Requirements: All_
  
  - [ ] 10.3 Create migration guide
    - Document changes from previous version
    - Provide examples of new behavior
    - Document breaking changes (if any)
    - _Requirements: All_

- [ ] 11. Final checkpoint - Run full test suite
  - Run all unit tests: `poetry run pytest tests/test_agent_orchestrator*.py`
  - Run all property tests: `poetry run pytest -m property`
  - Run integration tests: `poetry run pytest -m integration`
  - Run performance tests
  - Run with coverage: `poetry run pytest --cov=app/services/agent_orchestrator.py --cov-report=html`
  - Verify coverage >= 90% for modified code
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Deployment preparation
  - [ ] 12.1 Create deployment checklist
    - List all changes
    - List all tests
    - List rollback procedures
    - _Requirements: All_
  
  - [ ] 12.2 Prepare monitoring dashboards
    - Create dashboard for access control metrics
    - Create dashboard for performance metrics
    - Create dashboard for error rates
    - _Requirements: 4.3_
  
  - [ ] 12.3 Configure alerts
    - Set up critical alerts
    - Set up warning alerts
    - Test alert delivery
    - _Requirements: 4.3_

## Notes

- All Python commands should use `poetry run` prefix
- Each task should be tested before moving to the next
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- Performance tests ensure targets are met
- Access control is the highest priority (security-critical)
- Logging is essential for debugging and analytics
- Error messages should be clear and actionable

## Implementation Order Rationale

1. **Access control first**: Security-critical, must be correct
2. **Classification second**: Depends on access control context
3. **Logging third**: Needed for debugging other components
4. **route_query updates fourth**: Integrates all previous components
5. **Context loader fifth**: Depends on route_query changes
6. **Testing throughout**: Validate each component as it's built
7. **Documentation last**: After all functionality is complete

## Testing Strategy

- **Unit tests**: Test individual methods in isolation
- **Property tests**: Test universal properties with generated inputs (100+ iterations)
- **Integration tests**: Test complete flows across multiple components
- **Performance tests**: Verify latency and throughput targets
- **Coverage target**: 90%+ for modified code
- **Test execution**: Use `poetry run pytest` for all test commands

## Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Access Control Check | < 5ms | P95 latency |
| Classification | < 500ms | P95 latency (with caching) |
| Logging | < 1ms | P95 latency |
| Total Routing (Voice) | < 2s | P95 latency |
| Total Routing (Text) | < 3s | P95 latency |

## Deployment Checklist

Before deploying to staging/production:
- [ ] All tests passing
- [ ] Coverage >= 90%
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Monitoring dashboards created
- [ ] Alerts configured
- [ ] Rollback plan documented
- [ ] Team notified

## Success Criteria

- ✅ 100% access control enforcement (no bypasses)
- ✅ All error messages include context and corrective actions
- ✅ All routing decisions logged with required fields
- ✅ Performance targets met (< 2s voice, < 3s text)
- ✅ 90%+ test coverage for modified code
- ✅ Zero regressions in existing functionality
