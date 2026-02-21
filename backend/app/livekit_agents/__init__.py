"""
LiveKit Voice Agent Integration for Shuren Fitness Coaching.

This package contains the voice agent implementation that enables real-time
voice interactions between users and AI fitness coaches through LiveKit's
infrastructure. The voice agent integrates Speech-to-Text (Deepgram),
Text-to-Speech (Cartesia), and the existing LangChain agent orchestrator
for complex reasoning.

The voice agent achieves <2 second latency by pre-loading user context and
orchestrator before connecting to LiveKit rooms, using cached data for quick
queries, and processing workout logs asynchronously.
"""

from .voice_agent_worker import FitnessVoiceAgent

__all__ = [
    "FitnessVoiceAgent",
]
