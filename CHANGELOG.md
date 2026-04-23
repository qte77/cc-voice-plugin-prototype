# Changelog

## [Unreleased]

## [0.6.0] - 2026-04-23

## [0.5.0] - 2026-04-11

### Added
- feat(see): `cc_vlm` module with in-process `llama-cpp-python` backend — `/see` skill captures screen, runs a local VLM (Qwen2.5-VL default) with task-constrained prompt templates, returns a text description for Claude's prompt. ~120 tokens/call vs ~1,600 for raw vision (~13× reduction); 0 tokens on cache hits via BLAKE3 frame hash LRU. (#26)
- feat(see): `--image-file PATH` flag — describe a pre-captured image instead of capturing the screen; enables headless testing and saved-screenshot use cases. (#26)
- feat(see): five task-constrained prompt templates (terminal, editor, browser, gui, generic) capping VLM output length at the source. (#26)
- feat(see): `LlamaCppVLMEngine` supporting six model families via `_HANDLER_MAP` (qwen2.5vl, llava15, llava16, moondream, minicpmv, nanollava). (#26)
- build(make): `setup_user` target — end-user minimum install (package + best local TTS), no dev tools. `setup_all` clarified as "Developer happy path". (#28)
- build(make): `setup_see` target — installs `[see]` extras (mss, Pillow, blake3) and prints hardware-specific `llama-cpp-python` install commands (CPU / CUDA / Metal / ROCm). (#26)
- build(make): `plugin_validate`, `plugin_install_local`, `plugin_uninstall`, `plugin_list`, `run_cc` targets — full plugin-in-CC lifecycle for local dev. (#26)
- build(make): `smoke_imports`, `smoke_cli`, `smoke` targets — fast sanity checks that don't need external deps. (#26)
- build(make): `listen`, `see`, `see_file`, `see_save_only` direct-run targets (bypass CC for testing). (#26)
- build(make): `clean_models`, `clean_see_artifacts`, `clean_all` targets — remove downloaded VLM models, `/tmp` JPEGs, and full local reset. (#26)
- docs(roadmap): `docs/roadmap/v0.5.x.md` — living tracker for deferred ideas and rejected directions alongside filed issues. (#35)

### Changed
- fix(types): narrow `listen.py` config parameter to `STTConfig | None` (was `object`) — eliminates pyright strict errors without per-line suppressions. (#26)
- fix(stt): add `argparse` to `cc_stt/__main__.py` — `python -m cc_stt --help` now works; previously jumped straight to `listen_live()` and errored. Backward compat preserved for `python -m cc_stt hook` and file transcription. (#26)
- chore(build): `[project.optional-dependencies] all` now uses PEP 621 self-references (`cc-voice[piper]`, etc.) instead of duplicating every dep — fixed long-standing DRY violation. (#26)

## [0.4.0] - 2026-04-11

### Added
- feat(stt): live `/listen` pipeline — mic capture → VAD buffering → Moonshine/Vosk transcription → PTY injection (#14)
- feat(stt): file transcription mode via `transcribe_file()` (#14)
- feat(stt): `__main__.py` dispatcher routing to listen/transcribe/hook modes (#14)
- docs(vlm): ADR-0001 screen-sharing architecture for `/see` — three tiers (CC-native vision, local VLM, hybrid) (#18)
- docs(vlm): `/see` skill stub (status: research) (#18)
- build(make): `setup_all` happy-path target installing dev + TTS engines + STT deps (#19)
- build(make): `setup_stt` target using existing `[stt]` extras group (#19)
- build(make): `clean` target removing `.venv` + caches (#19)
- test: 9 listen pipeline tests — TestListenLive, TestTranscribeFile, TestMainDispatch (#14)
- test: 19 plugin config validation tests — plugin.json schema, marketplace source resolution (#13)

### Changed
- fix(types): adopt pyright strict + suppress-unknowns config — resolves untyped-library leakage from sounddevice / pydantic-settings; ported from sibling project Agents-eval (#19)
- fix(types): narrow `listen.py` config parameter to `STTConfig | None` instead of `object` (#14)
- chore(build): Makefile uses `uv sync` only — dropped `uv pip install` rule violations in `setup` and `setup_dev` (#19)
- chore(build): rename `setup_tts` → `setup_espeak` for accuracy (it installs espeak-ng + mpv, not TTS generically) (#19)
- chore(build): `test_coverage` now reports both `cc_tts` and `cc_stt` — previously silently dropped `cc_stt` (#19)
- chore(build): `wrap` help text now warns about bwrap sandbox deadlock per AGENT_LEARNINGS.md (#19)
- chore(gitignore): exclude `.coverage` artifact (#25)
- style: ruff format drift cleanup across 5 files (src/cc_stt/mic.py, test_plugin_config.py, test_stt_config.py, test_stt_engine.py, test_stt_mic.py) (#25)
- build(deps-dev): bump edge-tts ≥6.1.0 → ≥7.2.8 (#20)
- build(deps-dev): bump bump-my-version ≥0.29.0 → ≥1.3.0 (#21)

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
