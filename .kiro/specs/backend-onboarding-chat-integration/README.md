# Backend Onboarding Chat Integration

**Status:** ✅ Requirements Approved - Ready for Design Phase  
**Priority:** High  
**Owner:** Backend Team  
**Created:** 2026-02-11

---

## Quick Links

- **Requirements:** [requirements.md](./requirements.md)
- **Design:** [design.md](./design.md) _(coming soon)_
- **Tasks:** [tasks.md](./tasks.md) _(coming soon)_
- **Summary:** [docs/technichal/backend_onboarding_chat_integration_spec.md](../../../docs/technichal/backend_onboarding_chat_integration_spec.md)

---

## What This Spec Covers

This specification defines backend modifications to enable:

1. **Chat-based onboarding** with specialized AI agents
2. **9-state onboarding flow** (consolidated from 11 steps)
3. **Agent function tools** for data persistence
4. **Access control** based on onboarding status
5. **Rich progress tracking** for UI indicators

---

## Key Deliverables

### New API Endpoints
- `GET /api/v1/onboarding/progress` - Progress metadata
- `POST /api/v1/chat/onboarding` - Agent-driven onboarding

### Modified Endpoints
- `GET /api/v1/users/me` - Add access_control object
- `POST /api/v1/onboarding/step` - Support 9 states
- `POST /api/v1/chat` - Enforce agent restrictions

### Database Changes
- Update `OnboardingState` constraint (0-11 → 0-9)
- Migrate existing data (11 steps → 9 states)

### Service Layer
- `OnboardingService` updates for 9 states
- `AgentOrchestrator` routing logic
- Agent function tool implementations

---

## State-to-Agent Mapping

| State | Agent | Description |
|-------|-------|-------------|
| 1 | Workout Planning | Fitness Level Assessment |
| 2 | Workout Planning | Primary Fitness Goals |
| 3 | Workout Planning | Workout Preferences & Constraints |
| 4 | Diet Planning | Diet Preferences & Restrictions |
| 5 | Diet Planning | Fixed Meal Plan Selection |
| 6 | Scheduling & Reminder | Meal Timing Schedule |
| 7 | Scheduling & Reminder | Workout Schedule |
| 8 | Scheduling & Reminder | Hydration Schedule |
| 9 | Supplement Guidance | Supplement Preferences (Optional) |

---

## Implementation Timeline

- **Week 1:** Database schema & data migration
- **Week 2-3:** Backend implementation
- **Week 3:** Testing
- **Week 4:** Deployment

---

## Success Criteria

- ✅ All 9 states functional via chat
- ✅ Agent routing works correctly
- ✅ Access control enforced
- ✅ Progress tracking accurate
- ✅ Data migration successful
- ✅ Performance targets met (< 50ms progress, < 2s chat)
- ✅ 70% onboarding completion rate

---

## Next Steps

1. Review and approve requirements ✅
2. Create design.md with technical implementation
3. Create tasks.md with implementation checklist
4. Begin database migration
5. Implement backend changes
6. Test and deploy

---

## Questions or Feedback?

Contact: Backend Team  
Slack: #backend-dev  
Spec Location: `.kiro/specs/backend-onboarding-chat-integration/`
