# cc-tts (prototype)

> **Status: Prototype** — proof-of-concept for live TTS from Claude Code via PTY proxy. Not production-ready.

[![License](https://img.shields.io/badge/license-Apache--2.0-58f4c2.svg)](LICENSE.md)
![Version](https://img.shields.io/badge/version-0.1.0-58f4c2.svg)
[![CodeQL](https://github.com/qte77/cc-tts-plugin-protoype/actions/workflows/codeql.yaml/badge.svg)](https://github.com/qte77/cc-tts-plugin-protoype/actions/workflows/codeql.yaml)
[![CodeFactor](https://www.codefactor.io/repository/github/qte77/cc-tts-plugin-protoype/badge)](https://www.codefactor.io/repository/github/qte77/cc-tts-plugin-protoype)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-58f4c2.svg?logo=dependabot)](https://github.com/qte77/cc-tts-plugin-protoype/blob/main/.github/dependabot.yaml)
[![Link Checker](https://github.com/qte77/cc-tts-plugin-protoype/actions/workflows/links-fail-fast.yaml/badge.svg)](https://github.com/qte77/cc-tts-plugin-protoype/actions/workflows/links-fail-fast.yaml)

Text-to-speech output plugin for Claude Code. Speaks Claude's responses aloud using local/OSS TTS engines.

## Features

- **Live TTS via PTY proxy** — wraps interactive Claude Code with real-time sentence-chunked speech (`cc-tts-wrap claude`)
- **Batch TTS via Stop hook** — speaks full responses after completion (fallback for non-PTY environments)
- **Smart content filter** — strips ANSI escapes, code blocks, tool output, spinners; speaks only prose
- **Multi-engine** — espeak-ng (zero-config), Piper (neural), with engine auto-detection
- **On-demand `/speak` skill** — speak specific text or toggle auto-read mode

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

Create `.cc-tts.toml` in project root:

```toml
engine = "auto"              # "espeak" | "piper" | "kokoro" | "auto"
voice = "en_US-amy-medium"   # engine-specific voice name
speed = 1.0
auto_read = false            # enable Stop hook auto-read
max_chars = 2000
player = "auto"              # "mpv" | "ffplay" | "aplay" | "auto"
```

Environment overrides: `CC_TTS_ENGINE`, `CC_TTS_VOICE`, `CC_TTS_SPEED`, `CC_TTS_AUTO_READ`, `CC_TTS_PLAYER`.

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

Install as Claude Code plugin for `/speak` skill and Stop hook auto-read:

```bash
claude plugin install cc-tts@local
```

## License

[Apache-2.0](LICENSE.md)
