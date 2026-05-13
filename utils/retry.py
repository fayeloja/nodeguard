"""
utils/retry.py
--------------
Exponential backoff retry logic for LLM API calls.

Strategy: Full-Jitter Exponential Backoff
  wait = random(0, min(max_delay, base_delay * 2 ** attempt))

This avoids thundering-herd problems that pure exponential backoff can cause
when many concurrent requests hit the same rate-limit window.

Handles:
  - groq.RateLimitError / openai.RateLimitError
  - groq.APIStatusError / openai.APIStatusError  (e.g. 429, 529)
  - requests.exceptions.HTTPError (for raw HTTP layer errors)
  - Generic timeout/connection errors
"""

import functools
import random
import time
from typing import Callable, Any

from rich.console import Console

console = Console()

# Error classes are imported lazily so that missing optional packages
# (e.g. if only Groq is installed) don't raise ImportError at module load.
def _permanent_exceptions() -> tuple:
    """
    Return exception types that indicate a *permanent* failure and must
    NEVER be retried (e.g. bad API key, permission denied).
    Re-raising immediately saves time and gives the user a clear message.
    """
    exc_types = []
    try:
        import groq
        exc_types.append(groq.AuthenticationError)
        exc_types.append(groq.PermissionDeniedError)
    except (ImportError, AttributeError):
        pass
    try:
        import openai
        exc_types.append(openai.AuthenticationError)
        exc_types.append(openai.PermissionDeniedError)
    except (ImportError, AttributeError):
        pass
    return tuple(exc_types) if exc_types else ()


def _retryable_exceptions() -> tuple:
    """Return a tuple of exception types that should trigger a retry."""
    exc_types = []

    try:
        import groq
        exc_types.append(groq.RateLimitError)
        exc_types.append(groq.APIStatusError)
    except (ImportError, AttributeError):
        pass

    try:
        import openai
        exc_types.append(openai.RateLimitError)
        exc_types.append(openai.APIStatusError)
    except (ImportError, AttributeError):
        pass

    try:
        import requests
        exc_types.append(requests.exceptions.Timeout)
        exc_types.append(requests.exceptions.ConnectionError)
    except (ImportError, AttributeError):
        pass

    # Always catch generic timeout/OS errors
    import socket
    exc_types.append(socket.timeout)
    exc_types.append(TimeoutError)

    return tuple(exc_types) if exc_types else (Exception,)


def with_retry(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable:
    """
    Decorator factory that wraps a callable with retry + exponential backoff.

    Args:
        max_attempts: Total number of attempts (including the first one).
        base_delay:   Starting delay in seconds before the first retry.
        max_delay:    Maximum wait time in seconds (caps the backoff ceiling).

    Usage:
        @with_retry(max_attempts=5, base_delay=2.0)
        def call_llm(prompt):
            return llm.invoke(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            permanent = _permanent_exceptions()
            retryable = _retryable_exceptions()
            last_exc: Exception | None = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except BaseException as exc:
                    # ── Permanent errors: fail immediately, no retry ──────────
                    if permanent and isinstance(exc, permanent):
                        raise  # main.py prints the clean error message

                    # ── Only retry transient/rate-limit errors ───────────────
                    if not isinstance(exc, retryable):
                        raise

                    last_exc = exc
                    retries_left = max_attempts - attempt - 1

                    if retries_left == 0:
                        console.print(
                            f"\n[bold red]❌ All {max_attempts} attempts exhausted. "
                            f"Last error: {type(exc).__name__}: {exc}[/bold red]"
                        )
                        raise

                    # Full-jitter backoff
                    ceiling = min(max_delay, base_delay * (2 ** attempt))
                    wait = random.uniform(0, ceiling)

                    console.print(
                        f"[yellow]⚠️  Rate limit / API error on attempt "
                        f"{attempt + 1}/{max_attempts}: "
                        f"{type(exc).__name__}[/yellow]\n"
                        f"   Retrying in [bold]{wait:.1f}s[/bold] "
                        f"({retries_left} attempt{'s' if retries_left > 1 else ''} left)…"
                    )
                    time.sleep(wait)

            # Should never reach here, but satisfy type checkers
            raise last_exc  # type: ignore[misc]

        return wrapper
    return decorator
