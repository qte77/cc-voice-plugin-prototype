# Changelog

## [Unreleased]

## [0.4.0] - 2026-04-06

### Added
- feat(stt): live `/listen` pipeline — mic capture → VAD buffering → Moonshine/Vosk transcription → PTY injection
- feat(stt): file transcription mode via `transcribe_file()` 
- feat(stt): `__main__.py` dispatcher routing to listen/transcribe/hook modes
- test: 9 listen pipeline tests (TestListenLive, TestTranscribeFile, TestMainDispatch)
- test: 19 plugin config validation tests (plugin.json schema, marketplace source resolution)

### Fixed
- fix: plugin discovery — changed marketplace source from relative path to github source type (#7)
- fix: suppress CodeFactor B607/B108 warnings (#11)

## [0.3.0] - 2026-04-04

### Added

- `cc_stt` module with STTEngine protocol (Moonshine, Vosk) and auto-detection
- `STTConfig` with `.cc-voice.toml` [stt] section and `CC_STT_*` env overrides
- `MicCapture` with sounddevice streaming and `NoMicrophoneError` graceful degradation
- `UtteranceBuffer` with energy-based VAD, silence boundary detection, max duration timeout
- `inject_text()` PTY input for STT-to-stdin pipeline
- `should_auto_listen()` hook handler with graceful error fallback
- `/listen` skill definition (planned: live listen pipeline)
- 47 new tests (113 total) covering all STT modules
- `sounddevice>=0.5.0` as optional `stt` dependency

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
