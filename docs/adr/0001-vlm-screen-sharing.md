# ADR-0001: VLM Screen-Sharing Architecture for /see Command

## Status

Proposed

## Context

The cc-voice-plugin-prototype provides `/speak` (TTS) and `/listen` (STT) for
bidirectional voice interaction with Claude Code. The missing piece is **vision**:
sharing what the user sees on screen so Claude can reason about UI, code editors,
terminals, and error dialogs during pair programming or XP buddy sessions.

A `/see` command closes the voice+vision loop, enabling Claude to act as a fully
context-aware programming partner.

## Decision Drivers

- **Privacy-first**: local processing preferred, no mandatory cloud calls
- **Token efficiency**: minimize Vision API costs per screenshot
- **Latency**: < 2 s for interactive pair programming feedback
- **Dependency footprint**: heavy VLM runtimes must be optional
- **Pattern consistency**: follow the STT `Protocol`-based engine abstraction

## Considered Options

### Tier 1: CC-Native Vision (Recommended MVP)

- `python-mss` for cross-platform screen capture (Linux/macOS/Windows)
- Resize to <= 1568 px longest edge (Claude Vision sweet spot)
- JPEG compression (quality 85) -> ~100-200 KB per frame
- Send as base64 in `tool_result` image block to Claude Vision API
- ~1000 tokens per image at 1024x768
- Zero additional dependencies beyond `python-mss` and `Pillow`
- Latency: capture < 50 ms, API ~1-2 s

### Tier 2: Local VLM Processing

- Same capture pipeline as Tier 1
- Route through local VLM instead of Claude Vision API
- VLM generates text description -> inject as prompt context (no image tokens)
- Moondream2: 1.86 B params, ~2 s on CPU, good OCR capability
- Trade-off: lower reasoning quality, but zero API cost and full privacy

### Tier 3: Hybrid Pipeline

- Local VLM extracts structured data (OCR text, UI element tree, layout)
- Compressed thumbnail (256x192) + VLM summary sent to Claude
- Best of both: rich context at low token cost
- Most complex to implement and test

## Decision

Start with **Tier 1 (CC-native)** as the MVP. Add Tier 2 and Tier 3 as optional
engines following the STT engine `Protocol` pattern (`VLMEngine` protocol with an
`analyze()` method).

## Architecture

Pipeline: `ScreenCapture -> ImageProcessor -> VLMEngine -> inject`

Following the same patterns as STT (`STTEngine` protocol, `resolve_stt_engine`):

| Module | Responsibility |
|--------|---------------|
| `src/cc_vlm/capture.py` | `ScreenCapture` class wrapping `python-mss` |
| `src/cc_vlm/processor.py` | Resize, compress, region selection, base64 encoding |
| `src/cc_vlm/engine.py` | `VLMEngine` Protocol + `ClaudeVisionEngine` + `MoondreamEngine` |
| `src/cc_vlm/config.py` | `.cc-voice.toml` `[vlm]` section parsing |

Configuration:

```toml
[vlm]
engine = "auto"          # "claude" | "moondream" | "auto"
max_dimension = 1568     # longest edge in pixels
jpeg_quality = 85
region = "full"          # "full" | "active" | custom rect
```

Environment overrides: `CC_VLM_ENGINE`, `CC_VLM_MAX_DIMENSION`, `CC_VLM_REGION`.

## VLM Benchmarks

| Model | Params | Speed (CPU) | OCR Quality | License |
|-------|--------|-------------|-------------|---------|
| Moondream2 | 1.86 B | ~2 s | Good | Apache 2.0 |
| SmolVLM-256M | 256 M | ~500 ms | Basic | Apache 2.0 |
| Qwen2.5-VL-3B | 3 B | ~4 s | Excellent | Apache 2.0 |
| GLM-Edge-V-2B | 2 B | ~3 s | Good | Apache 2.0 |

Moondream2 is the recommended Tier 2 default: best balance of speed, quality,
and model size for on-device use.

## Consequences

### Positive

- Completes voice+vision loop — unique capability in the CC ecosystem
- Tier 1 MVP is minimal: two dependencies (`python-mss`, `Pillow`), ~200 LOC
- Protocol pattern makes engine swapping trivial (same as STT)

### Negative

- Tier 2/3 add significant optional dependencies (llama-cpp-python, model files)
- Claude Vision API costs ~1 K tokens per screenshot

### Risks

- Screen capture permissions vary by OS (macOS requires Screen Recording permission)
- Large model files for Tier 2 (~1-4 GB) affect first-run experience
