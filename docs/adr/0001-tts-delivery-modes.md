# ADR-0001: TTS Delivery Modes

**Status**: Accepted (2026-04-13)

## Context

Claude Code is an Ink-rendered terminal UI. Getting assistant text for TTS
has three paths with different trade-offs in interactivity, streaming, and
brittleness.

## Decision

**Stop hook** is the recommended default — clean JSON payload, full Ink UI,
zero terminal parsing. Post-response only (not mid-generation).

**Stream-json pipe** (`cc-tts-stream`) for non-interactive single-prompt use
with true mid-generation streaming.

**PTY proxy** parked — brittle, breaks on CC UI changes, high maintenance.
Keep code but do not promote.

**Bidirectional stream-json REPL** (`cc-tts-repl`) shipped as interactive
alternative without Ink UI. Verified working 2026-04-13.

## Rejected sources

- `--debug-file`: system logs only, no assistant text
- Session transcripts on disk: post-completion only, undocumented format

## Consequences

- Users get reliable TTS with Stop hook out of the box
- Mid-generation streaming requires giving up Ink UI (stream-json or REPL)
- PTY proxy code remains for potential future use but is unsupported
