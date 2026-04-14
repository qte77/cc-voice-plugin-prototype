# ADR-0002: TTS Delivery Modes

**Date**: 2026-04-13
**Status**: Accepted
**Context**: PR #49 post-mortem

## Problem

Claude Code is an Ink-rendered (React) terminal UI. Getting assistant text out of it for TTS has three distinct paths, each with trade-offs. We need a clear recommendation for users and a documented rationale for contributors.

## Delivery modes

### 1. Stop hook + sentence buffer (**recommended**)

**How**: CC fires a Stop hook after each assistant response. The hook receives a clean JSON payload with `last_assistant_message`. Our `hook_handler.py` spawns a detached TTS subprocess that uses `SentenceBuffer` to split the response into sentences and speak them sequentially.

**Pros**:
- Zero terminal parsing
- Full Ink UI preserved
- Works with any CC version (hook payload is stable API)
- Sentence-by-sentence playback starts ~1s after response completes

**Cons**:
- Not mid-generation streaming — text first appears in UI, then TTS starts
- First-sentence latency = Claude API completion + first TTS synthesis

**Use when**: Daily interactive use. This is the recommended default.

### 2. Stream-json pipe (`cc-tts-stream`)

**How**: `claude -p --output-format stream-json --include-partial-messages`. Non-interactive. We parse `content_block_delta` events with `text_delta` in real-time, feed to `SentenceBuffer`, speak.

**Pros**:
- True mid-generation streaming
- Clean structured JSON (no terminal parsing)
- Low fragility (stable API)

**Cons**:
- Single prompt → response → exit (no interactive session)
- No Ink UI

**Use when**: Piping text to Claude for a one-shot voice response (`cc-tts-stream "summarize this"`).

### 3. PTY proxy (`cc-tts-wrap claude`) — **legacy**

**How**: PTY-spawn interactive claude, scrape its terminal output (ANSI, CR, Ink rendering), try to extract prose via regex filters.

**Pros**:
- Interactive + Ink UI + mid-generation streaming (when filter works)

**Cons**:
- Brittle — breaks on any CC UI change (box-drawing chars, `\r\r\n` endings, cursor-right spacing, bullet markers for thinking vs response)
- State machine required to distinguish response text from thinking indicators
- High maintenance burden

**Use when**: You need all three (interactive + Ink + streaming) and accept breakage on CC updates. Currently parked.

## Comparison

| Mode | Interactive | Ink UI | Real streaming | Brittleness | Maintenance |
|------|-------------|--------|----------------|-------------|-------------|
| Stop hook | ✓ | ✓ | ✗ (post-response) | none | low |
| Stream-json | ✗ (single prompt) | ✗ | ✓ | low | low |
| PTY proxy | ✓ | ✓ | ✓ | high | high |

## Decision

**Default**: Stop hook + sentence buffer. Document as the recommended path in README.

**Secondary**: `cc-tts-stream` for non-interactive pipe use.

**Parked**: PTY proxy — keep code for now (issue-tracked for future decision), but do not promote as the primary path.

## Future direction: bidirectional stream-json REPL

Claude supports `--input-format stream-json` alongside `--output-format stream-json`. A thin Python REPL could accept user input, format as JSON messages, pipe to claude on stdin, and read streaming deltas on stdout — giving interactive streaming TTS without PTY parsing. Trade-off: no Ink UI (plain terminal).

Verified working 2026-04-13 via proof-of-concept. Not yet shipped.

## Potential cleaner interactive sources (unverified)

- **`claude --debug-file <path>`**: may write structured logs including assistant text deltas. Worth testing — if deltas present in real-time, could tail-watch for interactive streaming without PTY.
- **Session transcripts on disk**: CC stores session data under `~/.claude/projects/<hash>/sessions/<id>/`. File format undocumented; could contain streaming-friendly data. Worth investigating as a less-fragile alternative to PTY scraping.

These are parked for future investigation.

## References

- `src/cc_tts/hook_handler.py` — Stop hook handler
- `src/cc_tts/stream_json.py` — stream-json consumer
- `src/cc_tts/pty_proxy.py` — PTY proxy (legacy)
- `src/cc_tts/sentence_buffer.py` — shared sentence boundary detection
- `src/cc_tts/edge_stream.py` — streaming playback dispatcher
