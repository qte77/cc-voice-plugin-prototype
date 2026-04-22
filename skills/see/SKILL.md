---
name: see
description: Capture screen content and get a text description via an in-process VLM (llama-cpp-python). No daemon. Use for pair programming, reading terminal output, summarizing editor state, or sharing visual context with Claude with minimal token cost.
compatibility: Designed for Claude Code
metadata:
  allowed-tools: Bash, Read, Write
  argument-hint: [--template terminal|editor|browser|gui|generic] [--no-cache] [--save-only]
  context: inline
  stability: development
---

# /see

Capture the screen, run a local vision-language model (Qwen2.5-VL by default via llama-cpp-python), and return a short text description for injection into Claude's context. Token-efficient: ~120 tokens per call vs ~1,600 for sending the raw image to Claude's vision API. **No external daemon** — model runs in-process via llama-cpp-python.

## Install — three steps

```bash
# 1. Core scaffolding deps (mss, Pillow, blake3)
make setup_see

# 2. llama-cpp-python (pick ONE matching your hardware)
#    See `make setup_see` output for the exact commands.
#    Examples:
uv pip install 'llama-cpp-python' \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
# or CUDA 12.4:
# uv pip install 'llama-cpp-python' --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124
# or Metal:
# CMAKE_ARGS='-DLLAMA_METAL=on' uv pip install llama-cpp-python

# 3. Download the Qwen2.5-VL GGUF + mmproj files
mkdir -p ~/.cache/cc-voice/models
cd ~/.cache/cc-voice/models
wget https://huggingface.co/bartowski/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf
wget https://huggingface.co/bartowski/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf
```

Then configure `.cc-voice.toml`:

```toml
[vlm]
engine = "llamacpp"
model_path = "/home/USER/.cache/cc-voice/models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
mmproj_path = "/home/USER/.cache/cc-voice/models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"
handler_name = "qwen2.5vl"
```

## Usage

- `/see` — capture full screen, describe using the configured template (default: `generic`)
- `/see --template terminal` — constrained to terminal output (most recent command, exit status, errors)
- `/see --template editor` — code editor state (filename, cursor line, diagnostics)
- `/see --template browser` — page title, main heading, banners
- `/see --template gui` — active window, focused element, dialog text
- `/see --template generic` — free-form ≤100-word description
- `/see --no-cache` — bypass frame-hash cache; always call the VLM
- `/see --save-only` — capture + save JPEG, print the path, don't call the VLM
- `/see --monitor N` — capture specific monitor (default 1 = primary)
- `/see --image-file PATH` — describe a pre-captured image instead of capturing the screen. Use for saved screenshots, CI/headless runs, or environments where mss cannot access a display.

## Local testing without Claude Code

Two workflows for dev loops:

**Direct module invocation** (fastest, bypasses CC):

```bash
make see TEMPLATE=terminal           # capture + describe via live VLM
make see_file FILE=shot.jpg          # describe a pre-captured image (no display needed)
make see_save_only                   # capture + save JPEG, print path (no VLM call)
make smoke                           # imports + --help + full test suite
```

**Plugin installed into Claude Code** (full integration, uses CC slash commands):

```bash
make plugin_validate                 # sanity-check the manifest first
make plugin_install_local            # registers local marketplace + installs cc-voice (project scope)
make run_cc                          # starts claude; then type /see in the session
make plugin_uninstall                # removes plugin + marketplace when done
```

## Implementation

```bash
python -m cc_vlm $ARGUMENTS
```

## Configuration

Full `.cc-voice.toml` schema:

```toml
[vlm]
engine = "auto"                     # "auto" | "llamacpp"
model_path = ""                     # absolute path to .gguf vision model
mmproj_path = ""                    # absolute path to mmproj (CLIP projector) .gguf
handler_name = "qwen2.5vl"          # chat handler for this model family (see below)
n_ctx = 4096                        # context window
n_gpu_layers = 0                    # 0 = CPU only, -1 = all layers to GPU
max_tokens = 256                    # max VLM response tokens
max_dimension = 768                 # resize longest edge before VLM (tokens ∝ dimension²)
jpeg_quality = 85
template = "generic"                # default template if --template not passed
cache_size = 32                     # per-invocation LRU entries
```

**Supported handler_name values**:
- `qwen2.5vl` → `Qwen25VLChatHandler` (default, works with Qwen2.5-VL-2B/3B/7B)
- `llava15` → `Llava15ChatHandler` (LLaVA 1.5)
- `llava16` → `Llava16ChatHandler` (LLaVA 1.6)
- `moondream` → `MoondreamChatHandler` (Moondream2)
- `minicpmv` → `MiniCPMv26ChatHandler` (MiniCPM-V 2.6)
- `nanollava` → `NanollavaChatHandler`

Environment overrides: `CC_VLM_ENGINE`, `CC_VLM_MODEL_PATH`, `CC_VLM_MMPROJ_PATH`, `CC_VLM_HANDLER_NAME`, `CC_VLM_N_CTX`, `CC_VLM_N_GPU_LAYERS`, `CC_VLM_MAX_TOKENS`, `CC_VLM_MAX_DIMENSION`, `CC_VLM_JPEG_QUALITY`, `CC_VLM_TEMPLATE`, `CC_VLM_CACHE_SIZE`.

## Token budget

| Path | Tokens per call | Notes |
|---|---|---|
| `/see` (in-process VLM → text) | ~120 | Default. No daemon, no HTTP round-trip. |
| `/see` cache hit (unchanged screen) | 0 | Frame hashed via BLAKE3; same image+template = no VLM call |
| Sending raw image to Claude vision (Tier 1, deferred) | ~1,600 | Opt-in via future `--vision` flag |

Prompt templates cap the VLM's output length at the source (e.g., `terminal` says "Max 80 words. Fragments ok."), keeping injected context small regardless of screen content.

## Why llama-cpp-python and not Ollama

cc-voice prefers **lean w/o overhead**:
- **No persistent daemon** — nothing running when `/see` isn't being called (Ollama holds ~2.5 GB RAM idle)
- **No HTTP layer** — direct in-process Python call
- **No separate system service** — fewer moving parts, nothing to start/stop
- **~200-500 ms per-call** in the warm process (the ⭐ latency from ai-agents-research #84)

Trade-off: llama-cpp-python isn't in the `[see]` extras because the correct wheel depends on your hardware (CPU / CUDA / Metal / ROCm). You install the variant matching your machine manually. `make setup_see` prints the three common install commands.

## Removing changes made by `/see`

`/see` is stateless — each call is independent and leaves nothing persistent except the temp JPEG it writes and any cached model files you downloaded for the VLM. To fully remove:

| Artifact | Removal |
|---|---|
| Per-session cache (in-memory `DescribeCache`) | Exits with the Python process. Nothing to clean. |
| Temp JPEGs (`/tmp/tmp*.jpg`) | `make clean_see_artifacts` |
| Downloaded GGUF + mmproj (`~/.cache/cc-voice/models/`) | `make clean_models` |
| Python venv + pytest/ruff caches | `make clean` |
| All of the above at once | `make clean_all` |
| Plugin installation (if done via `make plugin_install_local`) | `make plugin_uninstall` |
| `llama-cpp-python` wheel | `uv pip uninstall llama-cpp-python` (manual since it's not in `[see]` extras) |

There is **no undo for past descriptions** that were injected into a Claude Code conversation — once text is in the conversation it stays in the conversation history. Only future behavior is controllable (via config or by not calling `/see` again).

## Status

Development — functional MVP. Ships `LlamaCppVLMEngine` only. The following are explicit follow-ups tracked in the 0.4.x hardening roadmap:

- **`OllamaVLMEngine`** — alternative backend for users who already run Ollama for other purposes (routing Claude Code, local chat) and want to reuse the daemon
- **`ClaudeVisionEngine`** (Tier 1 fallback) — opt-in `--vision` flag to send the raw JPEG to Claude's vision API for cases where the local VLM's text isn't enough
- **Crop to focused window** — OS-specific (xdotool / wlrctl / AppleScript) to auto-crop before VLM
- **Auto-template detection** — pick the right template from the focused window's class name
- **Persistent on-disk cache** — shared across processes (current cache is per-invocation)

See `docs/adr/0003-vlm-screen-sharing.md` for architectural decision.
