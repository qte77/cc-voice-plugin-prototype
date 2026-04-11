---
name: see
description: Capture screen content and get a text description via a local VLM (Ollama default). Use for pair programming, reading terminal output, summarizing editor state, or sharing visual context with Claude with minimal token cost.
compatibility: Designed for Claude Code
metadata:
  allowed-tools: Bash, Read, Write
  argument-hint: [--template terminal|editor|browser|gui|generic] [--no-cache] [--save-only]
  context: inline
  stability: development
---

# /see

Capture the screen, send it to a local vision-language model (Ollama + Qwen2.5-VL by default), and get a short text description that gets injected into Claude's context. Token-efficient: ~120 tokens per call vs ~1,600 for sending the raw image to Claude's vision API.

## Quick start

```bash
# one-time setup
make setup_see                               # installs Python deps
curl -fsSL https://ollama.com/install.sh | sh  # installs Ollama daemon
ollama pull qwen2.5vl:3b                     # one-time model download (~2.5 GB)
ollama serve &                               # daemon

# then use /see
/see                                         # default template, capture + describe
/see --template terminal                     # constrained to terminal output
/see --save-only                             # capture only, print file path
```

## Usage

- `/see` — capture full screen, describe using the configured template (default: `generic`)
- `/see --template terminal` — constrain VLM output to terminal-relevant fields (most recent command, exit status, errors)
- `/see --template editor` — code editor state (filename, cursor line, diagnostics)
- `/see --template browser` — page title, main heading, banners
- `/see --template gui` — active window, focused element, dialog text
- `/see --template generic` — free-form ≤100-word description
- `/see --no-cache` — bypass frame-hash cache; always call the VLM
- `/see --save-only` — capture + save JPEG, print the path, don't call the VLM (useful for manual inspection)

## Implementation

```bash
python -m cc_vlm $ARGUMENTS
```

## Configuration

Edit `.cc-voice.toml` in project root:

```toml
[vlm]
engine = "auto"                       # "auto" | "ollama"
endpoint = "http://localhost:11434"   # Ollama daemon URL
model = "qwen2.5vl:3b"                # any pulled Ollama vision model
max_dimension = 768                   # resize longest edge before VLM (tokens ∝ dimension²)
jpeg_quality = 85
template = "generic"                  # default template if --template not passed
cache_size = 32                       # per-invocation LRU entries
```

Environment overrides: `CC_VLM_ENGINE`, `CC_VLM_ENDPOINT`, `CC_VLM_MODEL`, `CC_VLM_MAX_DIMENSION`, `CC_VLM_JPEG_QUALITY`, `CC_VLM_TEMPLATE`, `CC_VLM_CACHE_SIZE`.

## Token budget

| Path | Tokens per call | Notes |
|---|---|---|
| `/see` (local VLM → text) | ~120 | Default |
| `/see` cache hit (unchanged screen) | 0 | Frame hashed via BLAKE3; same image+template = no VLM call |
| Sending raw image to Claude vision (Tier 1, deferred) | ~1,600 | Opt-in via future `--vision` flag |

Prompt templates cap the VLM's output length at the source (e.g., `terminal` says "Max 80 words. Fragments ok."), keeping injected context small regardless of screen content.

## Status

Development — functional MVP. Ships `OllamaVLMEngine` only. The following are explicit follow-ups tracked in the 0.4.x hardening roadmap:

- **`ClaudeVisionEngine`** (Tier 1 fallback) — opt-in `--vision` flag to send the raw JPEG to Claude's vision API for cases where the local VLM's text isn't enough
- **`LlamaCppServerVLMEngine`** — alternative backend for users who prefer llama-server's OpenAI-compatible API over Ollama
- **Crop to focused window** — OS-specific (xdotool / wlrctl / AppleScript) to auto-crop before VLM
- **Auto-template detection** — pick the right template from the focused window's class name
- **Persistent on-disk cache** — shared across processes (current cache is per-invocation)

See `docs/adr/0001-vlm-screen-sharing.md` for the architectural background. The MVP ships Tier 2 (local VLM → text) as the default rather than the ADR's original Tier 1 recommendation; the rationale is that token cost is the dominant UX concern for interactive `/see` use.
