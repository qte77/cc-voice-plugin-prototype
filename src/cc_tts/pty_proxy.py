"""PTY proxy for live TTS — wraps any command with real-time speech output."""

from __future__ import annotations

import atexit
import fcntl
import os
import pty
import queue
import select
import signal
import sys
import termios
import threading
import tty
from collections.abc import Callable
from typing import Any

from cc_tts.sentence_buffer import SentenceBuffer
from cc_tts.speak import synthesize_and_play
from cc_tts.stream_filter import StreamFilter


def _tts_worker(
    q: queue.Queue[str | None],
    *,
    on_speak: Callable[[str], None] | None = None,
) -> None:
    """Pull sentences from queue and speak them. Stops on None sentinel."""
    while True:
        sentence = q.get()
        if sentence is None:
            break
        try:
            if on_speak is not None:
                on_speak(sentence)
            else:
                synthesize_and_play(sentence)
        except Exception as exc:
            print(f"[cc-voice] TTS error: {exc}", file=sys.stderr)


def _get_winsize(fd: int) -> bytes:
    return fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\x00" * 8)


def _set_winsize(fd: int, winsize: bytes) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


def _spawn_child(args: list[str], master_fd: int, slave_fd: int) -> int:
    """Fork and exec the child process under the slave PTY. Returns child PID.

    FIXME codefactor.io: extracted from run_pty_proxy to reduce complexity from 16 to <10.
    """
    pid = os.fork()
    if pid == 0:
        os.close(master_fd)
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        os.execvp(args[0], args)  # noqa: S606  # FIXME codefactor.io B606: PTY must exec child directly
    return pid


def _setup_terminal(master_fd: int) -> tuple[int, bool, Any]:
    """Configure stdin raw mode if TTY. Returns (stdin_fd, is_tty, old_attrs).

    FIXME codefactor.io: extracted from run_pty_proxy to reduce complexity.
    """
    try:
        stdin_fd = sys.stdin.fileno()
        is_tty = os.isatty(stdin_fd)
    except (OSError, ValueError, AttributeError):
        return -1, False, None

    if not is_tty:
        return stdin_fd, False, None

    old_attrs = termios.tcgetattr(stdin_fd)
    tty.setraw(stdin_fd)
    atexit.register(termios.tcsetattr, stdin_fd, termios.TCSAFLUSH, old_attrs)

    try:
        _set_winsize(master_fd, _get_winsize(stdin_fd))
    except (OSError, termios.error):
        pass

    return stdin_fd, True, old_attrs


def _proxy_loop(master_fd: int, stdin_fd: int, is_tty: bool, stream_filter: StreamFilter) -> None:
    """Select loop proxying I/O between terminal and child PTY.

    FIXME codefactor.io: extracted from run_pty_proxy to reduce complexity.
    """
    fds = [stdin_fd, master_fd] if is_tty else [master_fd]
    while True:
        try:
            rfds, _, _ = select.select(fds, [], [])
        except (OSError, ValueError):
            break

        if stdin_fd in rfds and is_tty:
            try:
                data = os.read(stdin_fd, 4096)
            except OSError:
                break
            if not data:
                break
            os.write(master_fd, data)

        if master_fd in rfds:
            try:
                data = os.read(master_fd, 4096)
            except OSError:
                break
            if not data:
                break
            os.write(sys.stdout.fileno(), data)
            stream_filter.feed(data)


def run_pty_proxy(
    args: list[str],
    *,
    on_speak: Callable[[str], None] | None = None,
) -> int:
    """Run a command under a PTY proxy with live TTS.

    Args:
        args: Command and arguments to run (e.g., ["claude"]).
        on_speak: Optional callback for testing. If None, uses synthesize_and_play.

    Returns:
        Child process exit code.
    """
    master_fd, slave_fd = pty.openpty()
    pid = _spawn_child(args, master_fd, slave_fd)
    os.close(slave_fd)

    tts_queue: queue.Queue[str | None] = queue.Queue(maxsize=10)
    buf = SentenceBuffer(on_sentence=tts_queue.put, max_chars=2000)
    stream_filter = StreamFilter(buf)

    worker = threading.Thread(
        target=_tts_worker, args=(tts_queue,), kwargs={"on_speak": on_speak}, daemon=False
    )
    worker.start()

    stdin_fd, is_tty, old_attrs = _setup_terminal(master_fd)

    def _on_winsize(signum: int, frame: object) -> None:
        try:
            _set_winsize(master_fd, _get_winsize(sys.stdin.fileno()))
        except (OSError, termios.error):
            pass

    signal.signal(signal.SIGWINCH, _on_winsize)

    try:
        _proxy_loop(master_fd, stdin_fd, is_tty, stream_filter)
    except KeyboardInterrupt:
        pass
    finally:
        if old_attrs is not None:
            termios.tcsetattr(stdin_fd, termios.TCSAFLUSH, old_attrs)
        stream_filter.finish()
        tts_queue.put(None)
        try:
            worker.join(timeout=5)
        except KeyboardInterrupt:
            pass

    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def main() -> None:
    """CLI entry point for cc-tts-wrap."""
    if len(sys.argv) < 2:
        print("Usage: cc-tts-wrap <command> [args...]", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_pty_proxy(sys.argv[1:]))
