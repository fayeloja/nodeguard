"""
utils/cache.py
--------------
Content-hash based result cache for NodeGuard.

How it works:
  - Each file's content is hashed with SHA-256.
  - The hash is used as a cache key stored under .nodeguard_cache/<hash>.json.
  - Cache entries expire after CACHE_TTL_SECONDS (default 24 h via env).
  - If a cached result exists and is fresh, the full LLM pipeline is skipped.
"""

import hashlib
import json
import os
import time
from typing import Optional, Dict, Any

# TTL in seconds — overridable via env var NODEGUARD_CACHE_TTL
CACHE_TTL_SECONDS = int(os.getenv("NODEGUARD_CACHE_TTL", str(24 * 60 * 60)))
CACHE_DIR = os.getenv("NODEGUARD_CACHE_DIR", ".nodeguard_cache")


def _hash_content(content: str) -> str:
    """Return the SHA-256 hex digest of the given string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _cache_path(content_hash: str) -> str:
    return os.path.join(CACHE_DIR, f"{content_hash}.json")


def get_cached_result(content: str) -> Optional[Dict[str, Any]]:
    """
    Return the cached analysis dict for the given file content, or None
    if the cache entry is missing or expired.
    """
    content_hash = _hash_content(content)
    path = _cache_path(content_hash)

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)

        cached_at = entry.get("cached_at", 0)
        age = time.time() - cached_at

        if age > CACHE_TTL_SECONDS:
            # Stale — remove and treat as a miss
            os.remove(path)
            return None

        return entry.get("result")

    except (json.JSONDecodeError, OSError):
        return None


def save_cached_result(content: str, result: Dict[str, Any]) -> None:
    """
    Persist an analysis result keyed by the SHA-256 hash of the file content.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    content_hash = _hash_content(content)
    path = _cache_path(content_hash)

    entry = {
        "cached_at": time.time(),
        "content_hash": content_hash,
        "result": result,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)


def invalidate_cache(content: str) -> bool:
    """
    Remove the cache entry for the given content. Returns True if removed.
    """
    content_hash = _hash_content(content)
    path = _cache_path(content_hash)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def cache_stats() -> Dict[str, Any]:
    """Return a quick summary of the current cache state."""
    if not os.path.exists(CACHE_DIR):
        return {"entries": 0, "expired": 0, "valid": 0, "size_bytes": 0}

    entries = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    now = time.time()
    expired = 0
    total_size = 0

    for filename in entries:
        path = os.path.join(CACHE_DIR, filename)
        try:
            total_size += os.path.getsize(path)
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            if now - entry.get("cached_at", 0) > CACHE_TTL_SECONDS:
                expired += 1
        except (json.JSONDecodeError, OSError):
            expired += 1

    return {
        "entries": len(entries),
        "expired": expired,
        "valid": len(entries) - expired,
        "size_bytes": total_size,
    }
