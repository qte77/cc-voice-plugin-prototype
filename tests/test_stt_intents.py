"""Tests for cc_stt.intents — local intent matching."""

from __future__ import annotations

from cc_stt.intents import match_intent


class TestMatchIntent:
    def test_run_tests(self) -> None:
        assert match_intent("run tests") == (True, "make test")

    def test_run_the_test(self) -> None:
        assert match_intent("run the test") == (True, "make test")

    def test_show_last_commit(self) -> None:
        assert match_intent("show me the last commit") == (True, "git log -1 --oneline")

    def test_show_recent_commit(self) -> None:
        assert match_intent("show recent commit") == (True, "git log -1 --oneline")

    def test_git_status(self) -> None:
        assert match_intent("what's the status") == (True, "git status -s")

    def test_show_git_status(self) -> None:
        assert match_intent("show git status") == (True, "git status -s")

    def test_cancel(self) -> None:
        assert match_intent("cancel") == (True, None)

    def test_never_mind(self) -> None:
        assert match_intent("never mind") == (True, None)

    def test_stop(self) -> None:
        assert match_intent("stop") == (True, None)

    def test_no_match(self) -> None:
        assert match_intent("explain this function to me") == (False, None)

    def test_empty_input(self) -> None:
        assert match_intent("") == (False, None)

    def test_case_insensitive(self) -> None:
        assert match_intent("RUN TESTS") == (True, "make test")
