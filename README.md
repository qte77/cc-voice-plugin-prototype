# cc-voice (prototype)

> **Status: Prototype** — end-to-end voice for Claude Code. TTS output via PTY proxy, STT input module scaffolded (config, engine, mic, VAD, PTY injection). Not production-ready.

[![License](https://img.shields.io/badge/license-Apache--2.0-58f4c2.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-0.5.0-58f4c2.svg)
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

# Batch auto-read (Stop hook — set in .cc-voice.toml [tts])
# auto_read = true
```

## Configuration

Create `.cc-voice.toml` in project root:

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

TTS env overrides: `CC_TTS_ENGINE`, `CC_TTS_VOICE`, `CC_TTS_SPEED`, `CC_TTS_AUTO_READ`, `CC_TTS_MAX_CHARS`, `CC_TTS_PLAYER`.

STT env overrides: `CC_STT_ENGINE`, `CC_STT_LANGUAGE`, `CC_STT_WAKE_WORD`, `CC_STT_MIC_DEVICE`, `CC_STT_AUTO_LISTEN`.

## TTS delivery modes

Three paths for getting Claude's text to TTS, each with trade-offs:

| Mode | Interactive? | Ink UI? | Real streaming? | Brittleness | Entry point |
|------|-------------|---------|-----------------|-------------|-------------|
| **Stop hook** (recommended) | yes | yes | no (post-response) | none | `auto_read=true` in `.cc-voice.toml` |
| Stream-json pipe | no | no | yes | low | `cc-tts-stream "prompt"` |
| PTY proxy | yes | yes | yes (when working) | high — scrapes Ink output | `cc-tts-wrap claude` |

**Recommended for daily use**: Stop hook. Interactive Claude, full Ink UI, TTS fires after each response. The `SentenceBuffer` splits the full response into sentences so audio starts ~1s after response completes, not at the very end.

See [docs/adr/0001-tts-delivery-modes.md](docs/adr/0001-tts-delivery-modes.md) for the full architectural decision.

### Architecture diagrams

**Stop hook (recommended)**

```text
claude (interactive, Ink UI)
    ↓  response complete
.claude/settings.json hooks.Stop
    ↓  JSON: {"last_assistant_message": "..."}
hook_handler.py → load_config, check auto_read
    ↓  if auto_read=true: spawn detached
speak.py --stream → speak_streaming()
    ↓
edge_stream.py (per engine) → player stdin
```

**Stream-json pipe (non-interactive, single prompt)**

```text
cc-tts-stream "your prompt"
    ↓
claude -p --output-format stream-json --include-partial-messages
    ↓  newline-delimited JSON
stream_json.py → parse text_delta events
    ↓
sentence_buffer.py → sentences as they arrive
    ↓
tts_worker.py queue → speak_streaming() (streaming per engine)
```

**PTY proxy (legacy, Ink-dependent)**

```text
cc-tts-wrap claude
    ↓
PTY proxy (pty_proxy.py) ↔ claude (interactive)
    ↓  raw terminal bytes
stream_filter.py → ANSI strip, CR normalize, whitelist, code-block skip
    ↓
sentence_buffer.py → sentences on ". " / "? " / "! "
    ↓
speak.py → engine.synthesize() → player.play_audio()
```

### How to interrupt voice playback

```bash
uv run cc-tts --stop
```

Reads the PID file at `~/.cache/cc-voice/speak.pid` and sends SIGTERM to the whole process group (engine + player + children). Works for all delivery modes (Stop hook, stream-json, PTY proxy) — any mode writes the pidfile on start.

**Bind to a hotkey** (no code change needed). Pick a key not already used by your shell/editors. Common available choices: Alt+s, F8, Ctrl+\\:

```bash
# bash — Alt+s (\\es)
bind -x '"\es":"uv run cc-tts --stop"'

# zsh — Alt+s
cc-tts-stop() { uv run cc-tts --stop }
zle -N cc-tts-stop
bindkey '^[s' cc-tts-stop

# tmux — prefix + s (or global with -n)
bind-key s run-shell "uv run cc-tts --stop"
```

Avoid Ctrl+G (opens nano help), Ctrl+C (sends SIGINT), Ctrl+D (EOF), Ctrl+Z (suspend).

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
