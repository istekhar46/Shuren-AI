# Voice Session Mute/Unmute Feature

## Overview
Added microphone mute/unmute functionality to the voice session interface using the official LiveKit React SDK.

## Implementation

### Files Modified
1. `frontend/src/hooks/useVoiceSession.ts` - Added `toggleMicrophone` function
2. `frontend/src/components/voice/VoiceControls.tsx` - Added mute/unmute button
3. `frontend/src/pages/VoicePage.tsx` - Integrated mute state and toggle handler
4. `frontend/tests/unit/voice.unit.test.tsx` - Added comprehensive tests

### Technical Details

#### Hook Enhancement (`useVoiceSession.ts`)
```typescript
const toggleMicrophone = useCallback(async () => {
  if (!room) return;
  
  try {
    const currentState = room.localParticipant.isMicrophoneEnabled;
    await room.localParticipant.setMicrophoneEnabled(!currentState);
  } catch (err) {
    const errorMessage =
      err instanceof Error ? err.message : 'Failed to toggle microphone';
    setError(errorMessage);
    console.error('Error toggling microphone:', err);
  }
}, [room]);
```

#### UI Component (`VoiceControls.tsx`)
- Mute button appears only when session is active
- Visual feedback: Blue when unmuted, Gray when muted
- Emoji indicators: 🎤 (unmuted) / 🔇 (muted)
- Tooltip support for accessibility

#### State Management (`VoicePage.tsx`)
```typescript
const isMicrophoneEnabled = room?.localParticipant?.isMicrophoneEnabled ?? true;
```

## Usage

### User Flow
1. Start a voice session
2. Click the "🎤 Mute" button to mute your microphone
3. Click the "🔇 Unmute" button to unmute your microphone
4. The button state updates automatically based on microphone status

### API Reference
Based on official LiveKit documentation:
- `room.localParticipant.setMicrophoneEnabled(boolean)` - Control microphone state
- `room.localParticipant.isMicrophoneEnabled` - Get current microphone state

## Testing
All tests pass (31/31):
- VoiceControls component tests (11 tests)
- VoicePage integration tests (11 tests)
- Mute/unmute functionality tests (4 new tests)

## References
- [LiveKit Camera & Microphone Documentation](https://docs.livekit.io/home/client/tracks/publish/)
- [LiveKit JS Client SDK - LocalParticipant](https://docs.livekit.io/client-sdk-js/classes/LocalParticipant.html)
- [LiveKit Components React](https://github.com/livekit/components-js)
