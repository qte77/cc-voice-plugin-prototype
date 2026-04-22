# ADR-0003: VLM Screen-Sharing for /see Command

**Status**: Accepted (2026-04-11)

## Context

`/see` shares the user's screen with Claude for visual reasoning during
pair programming. Key constraint: token cost per screenshot must be low
enough for frequent interactive use.

## Decision

**Tier 2 (local VLM) as MVP** — `llama-cpp-python` with Qwen2.5-VL-3B
generates a text description (~120 tokens) injected as prompt context.

**Tier 1 (Claude Vision API) deferred** — ~1,600 tokens per raw image.
Token cost is the dominant UX concern for interactive `/see` use.

**Tier 3 (hybrid)** deferred — VLM summary + compressed thumbnail. Most
complex, defer until Tier 2 proves insufficient.

## Rejected

- **inferrs** — text-LLM only, no vision support
- **DPT-2 Mini** — cloud-only, English-only, preview status

## Consequences

- Zero API cost per screenshot (fully local)
- Cold-start ~3-5 s (model load), warm calls ~200-500 ms
- Large model files (1-4 GB) affect first-run experience
- BLAKE3 frame cache eliminates redundant VLM calls
