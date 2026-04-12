---
name: speak
description: Speak text aloud using local TTS. Use when the user wants Claude's output read aloud or to toggle auto-read mode.
compatibility: Designed for Claude Code
metadata:
  allowed-tools: Bash, Read
  argument-hint: [text to speak or --toggle]
  stability: development
---

# /speak

Speak text aloud using local text-to-speech.

## Usage

- `/speak Hello world` — speak specific text
- `/speak --toggle` — enable/disable auto-read mode
- `/speak --voice en_GB-alan` — use a specific voice

## Implementation

```bash
uv run python -m cc_tts.speak $ARGUMENTS
```

## Configuration

Edit `.cc-voice.toml` in project root:

```toml
[tts]
engine = "auto"              # "kokoro" | "piper" | "espeak" | "auto"
voice = "af_sarah"           # kokoro voice name
speed = 1.0
auto_read = false
max_chars = 2000
player = "auto"              # "mpv" | "ffplay" | "aplay" | "auto"
```

Environment overrides: `CC_TTS_ENGINE`, `CC_TTS_VOICE`, `CC_TTS_SPEED`, `CC_TTS_AUTO_READ`.

## TTS modes — batch vs streaming

Two ways to auto-speak Claude's responses. **Do not combine** — causes double speaking.

| Mode | Start with | First audio | How it works |
|---|---|---|---|
| **Batch (Stop hook)** | `/speak --toggle` or `make run_voice` | ~2-5s after response ends | Stop hook fires → handler forks (CC unblocks) → Kokoro synthesizes full text → plays |
| **Streaming (PTY proxy)** | `make run_voice_stream` | ~0.5s after first sentence | PTY wrapper intercepts stdout → speaks sentence-by-sentence as Claude types |

**Stop hook latency**: the handler forks immediately so CC accepts input while audio plays in the background. Synthesis time is proportional to response length (~1s per 100 words with Kokoro). For low-latency needs, use streaming mode.

## Voice Loop (STT + TTS)

Enable auto-read then use CC-native `/voice` for full bidirectional voice:

1. `/speak --toggle` (enables auto-read)
2. `/voice` (enables CC speech-to-text input)
3. Speak → Claude transcribes → responds → speaks response
