"""Tests for cc_vlm.cache — BLAKE3 image hash + LRU describe cache."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from cc_vlm.cache import DescribeCache, describe_with_cache, image_hash


class TestImageHash:
    def test_deterministic(self, tmp_path: Path) -> None:
        img = tmp_path / "a.jpg"
        img.write_bytes(b"constant content")
        assert image_hash(img) == image_hash(img)

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"content a")
        b.write_bytes(b"content b")
        assert image_hash(a) != image_hash(b)

    def test_hash_length_16_hex_chars(self, tmp_path: Path) -> None:
        img = tmp_path / "x.jpg"
        img.write_bytes(b"x")
        result = image_hash(img)
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)


class TestDescribeCache:
    def test_empty_cache_get_returns_none(self) -> None:
        cache = DescribeCache()
        assert cache.get("abc123", "prompt") is None

    def test_put_then_get(self) -> None:
        cache = DescribeCache()
        cache.put("abc", "prompt", "description")
        assert cache.get("abc", "prompt") == "description"

    def test_different_hash_different_entry(self) -> None:
        cache = DescribeCache()
        cache.put("abc", "prompt", "first")
        cache.put("def", "prompt", "second")
        assert cache.get("abc", "prompt") == "first"
        assert cache.get("def", "prompt") == "second"

    def test_different_prompt_different_entry(self) -> None:
        """Same image, different prompt, should be separate cache entries."""
        cache = DescribeCache()
        cache.put("abc", "terminal template", "terminal output")
        cache.put("abc", "editor template", "editor output")
        assert cache.get("abc", "terminal template") == "terminal output"
        assert cache.get("abc", "editor template") == "editor output"

    def test_lru_eviction(self) -> None:
        cache = DescribeCache(max_size=2)
        cache.put("a", "p", "one")
        cache.put("b", "p", "two")
        cache.put("c", "p", "three")  # should evict "a"
        assert cache.get("a", "p") is None
        assert cache.get("b", "p") == "two"
        assert cache.get("c", "p") == "three"

    def test_get_moves_to_most_recently_used(self) -> None:
        """Accessing an entry should save it from LRU eviction."""
        cache = DescribeCache(max_size=2)
        cache.put("a", "p", "one")
        cache.put("b", "p", "two")
        cache.get("a", "p")  # marks a as MRU
        cache.put("c", "p", "three")  # should now evict "b" (LRU)
        assert cache.get("a", "p") == "one"
        assert cache.get("b", "p") is None
        assert cache.get("c", "p") == "three"

    def test_put_existing_key_updates_and_refreshes(self) -> None:
        cache = DescribeCache(max_size=2)
        cache.put("a", "p", "v1")
        cache.put("b", "p", "v2")
        cache.put("a", "p", "v1-updated")  # refresh — should not evict
        cache.put("c", "p", "v3")  # evicts b (LRU after refresh of a)
        assert cache.get("a", "p") == "v1-updated"
        assert cache.get("b", "p") is None

    def test_len_and_clear(self) -> None:
        cache = DescribeCache()
        assert len(cache) == 0
        cache.put("a", "p", "v")
        cache.put("b", "p", "v")
        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0


class TestDescribeWithCache:
    def test_cache_miss_calls_engine(self, tmp_path: Path) -> None:
        img = tmp_path / "x.jpg"
        img.write_bytes(b"content")
        engine = MagicMock()
        engine.describe.return_value = "fresh description"
        cache = DescribeCache()

        result = describe_with_cache(img, "prompt", engine, cache)

        assert result == "fresh description"
        engine.describe.assert_called_once_with(img, "prompt")

    def test_cache_hit_skips_engine(self, tmp_path: Path) -> None:
        img = tmp_path / "x.jpg"
        img.write_bytes(b"content")
        engine = MagicMock()
        engine.describe.return_value = "first call"
        cache = DescribeCache()

        describe_with_cache(img, "prompt", engine, cache)
        engine.describe.return_value = "second call"  # would-be second result
        result = describe_with_cache(img, "prompt", engine, cache)

        assert result == "first call"  # cached
        assert engine.describe.call_count == 1  # only called once

    def test_same_image_different_prompts_both_call_engine(self, tmp_path: Path) -> None:
        img = tmp_path / "x.jpg"
        img.write_bytes(b"content")
        engine = MagicMock()
        engine.describe.side_effect = ["terminal result", "editor result"]
        cache = DescribeCache()

        r1 = describe_with_cache(img, "terminal", engine, cache)
        r2 = describe_with_cache(img, "editor", engine, cache)

        assert r1 == "terminal result"
        assert r2 == "editor result"
        assert engine.describe.call_count == 2
