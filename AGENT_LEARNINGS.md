# Agent Learnings

## PTY proxy: fork + thread deadlock in sandboxed/test environments

**Pattern**: `os.fork()` in a multi-threaded process (pytest, bwrap sandbox) causes deadlocks. The forked child inherits thread state in a broken/locked state.

**Solution**: The worker thread must start **after** `os.fork()` in the parent process only. In pytest, the test runner itself is multi-threaded, so fork-based PTY tests need `capsys` disabled or must run in a subprocess.

**Evidence**: Python 3.14 emits `DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the child`. Direct invocation (`python -c "from cc_tts.pty_proxy import run_pty_proxy; ..."`) works; `make wrap` via bwrap sandbox does not.

**How to apply**: Always test PTY proxy via direct Python invocation, not through sandboxed make recipes. For CI, use `uv run python -c` or a dedicated test script.

## espeak-ng vs Piper voice names are incompatible

**Pattern**: Piper uses `en_US-amy-medium` format. espeak-ng uses `en-us` format. Passing Piper voice names to espeak-ng causes `non-zero exit status 1`.

**Solution**: `EspeakEngine.synthesize()` detects Piper voice names (contain `_`) and falls back to `en-us` default. Each engine handles its own voice name mapping.

**How to apply**: When adding new engines, always validate voice name compatibility. Don't pass config.voice blindly to engines with different naming conventions.

## Piper CLI requires full model path, not voice name

**Pattern**: `piper --model en_US-amy-medium` fails. It needs the full path to the `.onnx` file: `piper --model /path/to/en_US-amy-medium.onnx`.

**Solution**: Download models to a known location (e.g., `/tmp/piper-models/`) and resolve the full path before passing to Piper CLI.

**How to apply**: `PiperEngine` should resolve voice names to downloaded model paths, not pass raw names.
