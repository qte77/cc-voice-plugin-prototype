# Audio Example Transcript

All three WAV files were generated from the same text using different TTS engines.

## Text

> Here is what we achieved in this session. We built a text-to-speech plugin for Claude Code from scratch. It started as a batch Stop hook approach, but after researching 8 existing community projects, we pivoted to a novel PTY proxy architecture. This intercepts Claude's terminal output in real-time, filters out code blocks, spinners, and tool output, then speaks only prose sentences. The plugin has 60 passing tests, strict type checking, and is installable as a Claude Code plugin.

## Engines

| File | Engine | Voice | Quality |
|------|--------|-------|---------|
| `cc-tts-espeak-ng-summary.wav` | espeak-ng 1.51 | en-us (default) | Rule-based, robotic |
| `cc-tts-piper-summary.wav` | Piper 1.4.2 | en_US-amy-medium (VITS) | Neural, natural |
| `cc-tts-kokoro-summary.wav` | Kokoro 2.3.0 | af_sarah | Neural, best local quality |

Generated 2026-04-04 during cc-tts-plugin prototype session.
