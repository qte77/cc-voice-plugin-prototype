# cc-voice (prototype)

> **Status: Prototype** — end-to-end voice for Claude Code. TTS output via PTY proxy, STT input module scaffolded (config, engine, mic, VAD, PTY injection). Not production-ready.

[![License](https://img.shields.io/badge/license-Apache--2.0-58f4c2.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-0.3.0-58f4c2.svg)
[![CodeQL](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/codeql.yaml/badge.svg)](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/codeql.yaml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/cc-voice-plugin-prototype/badge)](https://www.codefactor.io/repository/github/qte77/cc-voice-plugin-prototype)
[![Dependabot](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/dependabot/dependabot-updates)
[![Link Checker](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/links-fail-fast.yaml/badge.svg)](https://github.com/qte77/cc-voice-plugin-prototype/actions/workflows/links-fail-fast.yaml)

End-to-end voice plugin for Claude Code. TTS speaks Claude's responses aloud, STT captures voice input via Moonshine/Vosk.

## Features

### TTS (text-to-speech)

- **Live TTS via PTY proxy** — wraps interactive Claude Code with real-time sentence-chunked speech (`cc-tts-wrap claude`)
- **Batch TTS via Stop hook** — speaks full responses after completion (fallback for non-PTY environments)
- **Smart content filter** — strips ANSI escapes, code blocks, tool output, spinners; speaks only prose
- **Multi-engine TTS** — Kokoro (best), Piper (neural), espeak-ng (zero-config), auto-detection
- **On-demand `/speak` skill** — speak specific text or toggle auto-read mode

### STT (speech-to-text)

- **STTEngine protocol** — Moonshine (27M params, ~400ms) and Vosk (50MB) with auto-detection
- **Mic capture** — sounddevice streaming with `NoMicrophoneError` graceful degradation
- **Utterance buffer** — energy-based VAD with silence boundary detection and max duration timeout
- **PTY injection** — transcribed text written to master PTY fd for child process stdin
- **On-demand `/listen` skill** — voice input and offline transcription (planned)

## Audio Examples

Session summary generated with three engines for comparison:

| Engine | Quality | File |
|--------|---------|------|
| espeak-ng | Robotic (rule-based) | [assets/audio/cc-tts-summary-espeak-ng.wav](assets/audio/cc-tts-summary-espeak-ng.wav) |
| Piper (amy) | Natural (neural VITS, ~60MB) | [assets/audio/cc-tts-summary-piper.wav](assets/audio/cc-tts-summary-piper.wav) |
| Kokoro (sarah) | Best local (82M params) | [assets/audio/cc-tts-summary-kokoro.wav](assets/audio/cc-tts-summary-kokoro.wav) |

## Quick Start

```bash
make setup_dev    # install package + dev deps
make setup_tts    # install espeak-ng + mpv (robotic, zero-config)
make setup_piper  # install Piper (neural, good quality)
make setup_kokoro # install Kokoro (best local quality)

# Live TTS (PTY wrapper — real-time)
cc-tts-wrap claude

# On-demand TTS (CLI)
cc-tts "Hello from Claude Code"

# Batch auto-read (Stop hook — set in .cc-tts.toml)
# auto_read = true
```

## Configuration

Create `.cc-voice.toml` in project root (also reads legacy `.cc-tts.toml`):

```toml
engine = "auto"              # "espeak" | "piper" | "kokoro" | "auto"
voice = "en_US-amy-medium"   # engine-specific voice name
speed = 1.0
auto_read = false            # enable Stop hook auto-read
max_chars = 2000
player = "auto"              # "mpv" | "ffplay" | "aplay" | "auto"

[stt]
engine = "auto"              # "moonshine" | "vosk" | "auto"
language = "en"
wake_word = "hey_claude"
mic_device = "default"
auto_listen = false
```

TTS env overrides: `CC_TTS_ENGINE`, `CC_TTS_VOICE`, `CC_TTS_SPEED`, `CC_TTS_AUTO_READ`, `CC_TTS_PLAYER`.

STT env overrides: `CC_STT_ENGINE`, `CC_STT_LANGUAGE`, `CC_STT_WAKE_WORD`, `CC_STT_MIC_DEVICE`, `CC_STT_AUTO_LISTEN`.

## Architecture

```text
cc-tts-wrap claude
    ↓
PTY proxy (pty_proxy.py) ↔ claude (interactive)
    ↓
stream_filter.py → ANSI strip, code block skip, spinner suppress
    ↓
sentence_buffer.py → accumulate, flush on ". " / "? " / "! "
    ↓
speak.py → engine.synthesize() → player.play_audio()
```

## Development

```bash
make validate       # lint + type check + test (quiet)
make quick_validate # lint + type check only
VERBOSE=1 make test # full pytest output
```

## CC Plugin

Install as Claude Code plugin for `/speak`, `/listen` skills and Stop hook auto-read:

```bash
claude plugin install cc-voice@local
```

## License

[Apache-2.0](LICENSE)
