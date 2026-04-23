---
name: listen
description: Transcribe speech using local STT. Use when the user wants voice input or offline audio transcription.
compatibility: Designed for Claude Code
metadata:
  allowed-tools: Bash, Read
  argument-hint: [audio-file.wav] or --toggle
  stability: development
---

# /listen

Transcribe speech using local speech-to-text.

## Usage

- `/listen` — start/stop listening via microphone
- `/listen recording.wav` — transcribe an audio file
- `/listen --toggle` — enable/disable auto-listen mode

## Implementation

```bash
python -m cc_stt $ARGUMENTS
```

## Configuration

Edit `.cc-voice.toml` in project root:

```toml
[stt]
engine = "auto"          # "moonshine" | "vosk" | "auto"
language = "en"
wake_word = "hey_claude"
mic_device = "default"
auto_listen = false
strip_fillers = true     # remove "um", "uh", "like", etc. before sending to LLM
intent_match = true      # match common commands locally (skip LLM)
max_words = 200          # hard word cap on transcriptions
```

Environment overrides: `CC_STT_ENGINE`, `CC_STT_LANGUAGE`, `CC_STT_WAKE_WORD`, `CC_STT_MIC_DEVICE`, `CC_STT_AUTO_LISTEN`, `CC_STT_STRIP_FILLERS`, `CC_STT_INTENT_MATCH`, `CC_STT_MAX_WORDS`.

## Status

Prototype — config, engine protocol, mic capture, utterance buffer, PTY injection, and live listen pipeline are implemented.
