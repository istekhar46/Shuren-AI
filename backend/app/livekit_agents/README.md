# LiveKit Voice Agent

Real-time voice interaction agent for Shuren fitness coaching.

## Overview

The LiveKit voice agent provides real-time voice coaching through LiveKit's infrastructure, integrating:
- **STT (Speech-to-Text)**: Deepgram for transcribing user speech
- **TTS (Text-to-Speech)**: Cartesia for generating voice responses
- **LLM**: Configurable (OpenAI, Anthropic, or Google) for natural language understanding
- **Agent Orchestrator**: LangChain-based orchestrator for complex reasoning

## Architecture

```
User Voice Input
    ↓
Deepgram STT → Transcription
    ↓
LLM Processing → Function Tools
    ↓
    ├─→ Quick Queries (cached data)
    │   ├─ get_todays_workout()
    │   ├─ get_todays_meals()
    │   └─ log_workout_set()
    │
    └─→ Complex Queries → LangChain Orchestrator
        ├─ Workout Planning Agent
        ├─ Diet Planning Agent
        └─ Supplement Guidance Agent
    ↓
Cartesia TTS → Voice Response
    ↓
User Hears Response
```

## Files

- `voice_agent_worker.py` - Main worker implementation
- `start_worker.bat` - Windows startup script
- `start_worker.sh` - Linux/Mac startup script
- `README.md` - This file

## Quick Start

### 1. Configure Environment

Add to `backend/.env`:

```bash
# LiveKit Server
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_WORKER_NUM_IDLE=2

# Voice Services
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key

# LLM Configuration
VOICE_LLM_PROVIDER=openai  # or anthropic, google
OPENAI_API_KEY=your_openai_key  # if using OpenAI
ANTHROPIC_API_KEY=your_anthropic_key  # if using Anthropic
GOOGLE_API_KEY=your_google_key  # if using Google

# Voice Agent Settings
VOICE_CONTEXT_CACHE_TTL=3600  # Cache user context for 1 hour
VOICE_MAX_RESPONSE_TOKENS=150  # Keep responses concise
```

### 2. Start the Worker

**Windows:**
```bash
cd backend
app\livekit_agents\start_worker.bat
```

**Linux/Mac:**
```bash
cd backend
./app/livekit_agents/start_worker.sh
```

**Manual (any platform):**
```bash
cd backend
poetry run python app/livekit_agents/voice_agent_worker.py dev
```

### 3. Verify Worker Status

Successful startup shows:
```
INFO … livekit.agents     starting worker  {"version": "1.4.1"}
INFO … livekit.agents     HTTP server listening on :XXXXX
INFO … livekit.agents     registered worker  {"agent_name": "", "id": "AW_..."}
```

## Development

### Running in Dev Mode

Dev mode includes:
- Hot-reload on file changes
- Detailed logging
- File watcher for automatic restarts

```bash
poetry run python app/livekit_agents/voice_agent_worker.py dev
```

### Running in Production Mode

Production mode:
- No hot-reload
- Optimized logging
- Stable for long-running processes

```bash
poetry run python app/livekit_agents/voice_agent_worker.py start
```

## Agent Types

The worker supports specialized agent types:

- `general` - General fitness assistant (default)
- `workout` - Workout coaching specialist
- `diet` - Nutrition coaching specialist
- `supplement` - Supplement guidance specialist

Agent type is specified in room metadata when creating a LiveKit room.

## Function Tools

The voice agent provides these function tools for quick responses:

### get_todays_workout()
Returns today's workout plan from cached user context.

**Use cases:**
- "What's my workout today?"
- "What exercises should I do?"

### get_todays_meals()
Returns today's meal plan from cached user context.

**Use cases:**
- "What should I eat today?"
- "What's on my meal plan?"

### log_workout_set(exercise, reps, weight)
Logs a completed workout set asynchronously.

**Use cases:**
- "I just did 10 reps of bench press at 135 pounds"
- "Log 12 squats at 185"

### ask_specialist_agent(query, specialist)
Delegates complex queries to specialized LangChain agents.

**Use cases:**
- Complex workout programming questions
- Detailed nutrition analysis
- Supplement protocols

## Performance

The agent achieves <2 second latency by:

1. **Pre-loading context** - User context loaded before room connection
2. **Cached data** - Quick queries use cached workout/meal plans
3. **Async logging** - Workout logs queued for background processing
4. **Warm LLM connection** - LLM pre-warmed during initialization

## Troubleshooting

### Worker won't start

**Error: "ws_url is required, or add LIVEKIT_URL in your environment"**
- Solution: Add LIVEKIT_URL to `.env` file
- Verify `.env` file exists in `backend/` directory

**Error: "ModuleNotFoundError: No module named 'app'"**
- Solution: Run from `backend/` directory
- Use: `cd backend && poetry run python app/livekit_agents/voice_agent_worker.py dev`

### Worker starts but doesn't connect

**Check LiveKit credentials:**
```bash
# Verify credentials in .env
LIVEKIT_URL=wss://...  # Must start with wss://
LIVEKIT_API_KEY=...    # Must be valid API key
LIVEKIT_API_SECRET=... # Must be valid API secret
```

**Check network connectivity:**
- Ensure firewall allows WebSocket connections
- Verify LiveKit server is accessible

### Voice quality issues

**Poor transcription accuracy:**
- Check Deepgram API key is valid
- Verify microphone input quality
- Consider using Deepgram's `nova-2-general` model (default)

**Robotic or slow TTS:**
- Check Cartesia API key is valid
- Adjust TTS speed in worker configuration
- Consider different Cartesia voice models

## Monitoring

### Worker Logs

The worker logs important events:
- Worker startup and registration
- Room connections
- User context loading
- Function tool calls
- Orchestrator delegations
- Errors and warnings

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages with stack traces

## Production Deployment

For production deployment:

1. **Use production mode:**
   ```bash
   poetry run python app/livekit_agents/voice_agent_worker.py start
   ```

2. **Run as a service:**
   - Use systemd (Linux) or Windows Service
   - Configure auto-restart on failure
   - Set up log rotation

3. **Scale horizontally:**
   - Run multiple worker instances
   - LiveKit automatically load-balances
   - Set `LIVEKIT_WORKER_NUM_IDLE` appropriately

4. **Monitor health:**
   - Check worker registration status
   - Monitor HTTP server endpoint
   - Track error rates and latency

## API Reference

See `voice_agent_worker.py` for detailed docstrings on:
- `FitnessVoiceAgent` class
- Function tools
- Entrypoint function
- Configuration options
