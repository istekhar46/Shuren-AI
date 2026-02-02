# User Journey Reference

This steering file includes the complete user journey documentation that describes how the finished Shuren product will work end-to-end.

## Reference Document

The complete user journey is documented in:
#[[file:../../docs/product/how_completed_product_will_look.md]]

## Key Flows to Reference

When implementing features, always refer to the user journey document for:

1. **Onboarding Flow** - Voice/text onboarding with LiveKit integration
2. **Workout Coaching** - Real-time voice guidance during exercises
3. **Meal Planning** - Interactive meal plan management and substitutions
4. **Adaptive Planning** - Automatic plan adjustments based on user behavior
5. **Progress Tracking** - Analytics and trend detection
6. **Agent Orchestration** - How queries route to specialized agents

## Implementation Principles from User Journey

- **Natural Interaction**: Support both voice and text modalities
- **Real-time Updates**: Database changes reflected immediately
- **Context-Aware**: Agents load full user context before responding
- **Proactive Adaptation**: Background tasks detect patterns and adjust plans
- **No Guilt**: System adapts to reality without penalizing users

## Technical Patterns

Every user interaction follows this flow:
1. User Action → FastAPI Endpoint
2. LiveKit Room Created (for voice/text sessions)
3. Agent Worker loads context from PostgreSQL/Redis
4. LLM processes with specialized prompts + tools
5. Agent uses @llm_functions to query/update database
6. Response generated (text or voice)
7. Database updated
8. Celery tasks handle background work

When implementing any feature, ensure it aligns with these patterns and the detailed flows in the user journey document.
