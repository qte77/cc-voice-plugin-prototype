# cc-tts

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
| espeak-ng | Robotic (rule-based) | [assets/audio/cc-tts-espeak-ng-summary.wav](assets/audio/cc-tts-espeak-ng-summary.wav) |
| Piper (amy) | Natural (neural VITS, ~60MB) | [assets/audio/cc-tts-piper-summary.wav](assets/audio/cc-tts-piper-summary.wav) |
| Kokoro (sarah) | Best local (82M params) | [assets/audio/cc-tts-kokoro-summary.wav](assets/audio/cc-tts-kokoro-summary.wav) |

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

```
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

MIT
