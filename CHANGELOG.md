# Changelog

## [Unreleased]

## [0.2.0] - 2026-04-04

### Changed

- Renamed from cc-tts to cc-voice (end-to-end voice scope)
- Config file: `.cc-voice.toml` (reads legacy `.cc-tts.toml` as fallback)
- Plugin name: `cc-voice` in plugin.json and marketplace.json

## [0.1.0] - 2026-04-04

### Added

- PTY proxy for live streaming TTS (`cc-tts-wrap`) with sentence-chunked pipeline
- Stream filter: ANSI stripping, code block skip, spinner suppress, tool output skip
- Sentence buffer with boundary detection and flush callback
- TTS engine abstraction with Kokoro, Piper, espeak-ng support and auto-detection
- Model auto-download for Piper (HuggingFace) and Kokoro (GitHub releases)
- Audio player with mpv/ffplay/aplay fallback chain and no-audio-device handling
- Text preprocessor: markdown, code blocks, URLs stripped for clean speech
- Stop hook handler for batch auto-read mode (`hooks/hooks.json`)
- `/speak` skill for on-demand TTS in Claude Code
- Configuration via `.cc-tts.toml` with environment variable overrides
- CC plugin manifest with marketplace.json for local install
- Audio examples comparing espeak-ng, Piper, and Kokoro engines (`assets/audio/`)
- Makefile with quiet-by-default validation (ruff, pyright strict, pytest)
- CI: CodeQL, Dependabot, lychee link checker
- Apache-2.0 license
- 65 tests covering all modules
