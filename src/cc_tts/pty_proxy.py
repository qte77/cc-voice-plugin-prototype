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
        if on_speak is not None:
            on_speak(sentence)
        else:
            synthesize_and_play(sentence)


def _get_winsize(fd: int) -> bytes:
    return fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\x00" * 8)


def _set_winsize(fd: int, winsize: bytes) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


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

    # Set initial window size from real terminal (if available)
    try:
        winsize = _get_winsize(sys.stdin.fileno())
        _set_winsize(master_fd, winsize)
    except (OSError, termios.error):
        pass

    pid = os.fork()

    if pid == 0:
        # Child: become session leader, attach to slave PTY, exec command
        os.close(master_fd)
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        if slave_fd > 2:
            os.close(slave_fd)
        os.execvp(args[0], args)

    # Parent: proxy I/O
    os.close(slave_fd)

    # TTS pipeline
    tts_queue: queue.Queue[str | None] = queue.Queue(maxsize=10)
    buf = SentenceBuffer(on_sentence=tts_queue.put, max_chars=2000)
    stream_filter = StreamFilter(buf)

    worker = threading.Thread(
        target=_tts_worker,
        args=(tts_queue,),
        kwargs={"on_speak": on_speak},
        daemon=True,
    )
    worker.start()

    # SIGWINCH forwarding
    def _on_winsize(signum: int, frame: object) -> None:
        try:
            _set_winsize(master_fd, _get_winsize(sys.stdin.fileno()))
        except (OSError, termios.error):
            pass

    signal.signal(signal.SIGWINCH, _on_winsize)

    # Save and set raw mode on stdin (if it's a TTY)
    try:
        stdin_fd = sys.stdin.fileno()
        is_tty = os.isatty(stdin_fd)
    except (OSError, ValueError, AttributeError):
        stdin_fd = -1
        is_tty = False
    old_attrs = None
    if is_tty:
        old_attrs = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
        atexit.register(termios.tcsetattr, stdin_fd, termios.TCSAFLUSH, old_attrs)

    try:
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
    finally:
        if old_attrs is not None:
            termios.tcsetattr(stdin_fd, termios.TCSAFLUSH, old_attrs)

        stream_filter.finish()
        tts_queue.put(None)  # stop worker
        worker.join(timeout=30)

    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def main() -> None:
    """CLI entry point for cc-tts-wrap."""
    if len(sys.argv) < 2:
        print("Usage: cc-tts-wrap <command> [args...]", file=sys.stderr)
        sys.exit(1)
    sys.exit(run_pty_proxy(sys.argv[1:]))
