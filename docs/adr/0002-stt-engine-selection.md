# ADR-0002: STT Engine Selection

**Status**: Accepted (2026-04-11)

## Context

`/listen` needs a local speech-to-text engine for privacy-first voice input.
Engine must run on CPU without cloud calls, with < 2 s latency for
interactive pair programming.

## Decision

**Moonshine** as default — fastest cold-start (~1 s), good accuracy for
English commands and code terminology. ONNX runtime, no GPU required.

**Vosk** as fallback — broader language support, smaller models, works
offline. Slightly lower accuracy for technical speech.

Auto-detect priority: Moonshine > Vosk.

## Deferred

- **Whisper** via faster-whisper (#31) — enables domain fine-tunes but
  heavier runtime. Add when users need custom vocabulary.
- **Parakeet-TDT** via onnx-asr (#32) — multilingual, CC-BY-4.0. Add
  when multilingual STT is needed.

## Consequences

- Zero-config STT for English users (Moonshine auto-detected)
- VAD buffering prevents partial utterance submission
- Engine protocol makes adding Whisper/Parakeet a single-file change
