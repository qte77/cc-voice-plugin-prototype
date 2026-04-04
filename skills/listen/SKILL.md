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

Transcribe speech using local speech-to-text (planned).

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
```

Environment overrides: `CC_STT_ENGINE`, `CC_STT_LANGUAGE`, `CC_STT_WAKE_WORD`, `CC_STT_MIC_DEVICE`, `CC_STT_AUTO_LISTEN`.

## Status

Prototype — config, engine protocol, mic capture, utterance buffer, and PTY injection are implemented. Live listen pipeline integration is planned.
