"""Frame-hash LRU cache for VLM describe() results.

Skipping the VLM call when the screen hasn't changed is the single biggest
token-saving lever for /see. Repeat calls on static screens return cached
text with 0 additional VLM tokens.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

from blake3 import blake3

if TYPE_CHECKING:
    from cc_vlm.engine import VLMEngine


def image_hash(image_path: Path) -> str:
    """Compute a short BLAKE3 hash of the image file for cache keying.

    16 hex chars = 64 bits. Ample entropy for an in-memory LRU with
    max_size in the tens; collisions would require adversarial input.
    """
    digest = blake3(image_path.read_bytes()).hexdigest()
    return digest[:16]


class DescribeCache:
    """LRU cache mapping (image_hash, prompt_template) → VLM description.

    Uses OrderedDict.move_to_end for O(1) LRU updates. Bounded by
    `max_size`; oldest entries evicted first.
    """

    def __init__(self, max_size: int = 32) -> None:
        self.max_size = max_size
        self._store: OrderedDict[tuple[str, str], str] = OrderedDict()

    def get(self, img_hash: str, prompt: str) -> str | None:
        """Return cached description or None on miss."""
        key = (img_hash, prompt)
        if key not in self._store:
            return None
        # Move to end → marks as most recently used
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, img_hash: str, prompt: str, description: str) -> None:
        """Store a description, evicting the oldest entry if at capacity."""
        key = (img_hash, prompt)
        if key in self._store:
            self._store.move_to_end(key)
            self._store[key] = description
            return
        self._store[key] = description
        if len(self._store) > self.max_size:
            self._store.popitem(last=False)

    def __len__(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()


def describe_with_cache(
    image_path: Path,
    prompt: str,
    engine: VLMEngine,
    cache: DescribeCache,
) -> str:
    """Return a cached description for the given image+prompt, or call engine on miss.

    Side effect: populates the cache on miss.
    """
    img_hash = image_hash(image_path)
    cached = cache.get(img_hash, prompt)
    if cached is not None:
        return cached
    description = engine.describe(image_path, prompt)
    cache.put(img_hash, prompt, description)
    return description
