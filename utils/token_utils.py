"""
utils/token_utils.py
--------------------
Utilities for keeping LLM token usage under control.

truncate_code   — trim code to a character budget, preserving the top of the file
                  where imports, config, and key logic usually live.
estimate_tokens — rough heuristic (chars / 4) for logging/debug purposes only.
"""

from typing import Optional

# Default character budget per prompt code block (≈ 1 000 tokens).
# Override via the MAX_CODE_CHARS env var.
import os
DEFAULT_MAX_CHARS = int(os.getenv("NODEGUARD_MAX_CODE_CHARS", "4000"))


def truncate_code(code: str, max_chars: Optional[int] = None) -> str:
    """
    Return code truncated to *max_chars* characters.

    If the code fits within the budget it is returned unchanged.
    Otherwise the first max_chars characters are kept and a clear
    truncation marker is appended so the LLM knows context was cut.

    Args:
        code:      The JavaScript/Node.js source code string.
        max_chars: Character limit. Defaults to DEFAULT_MAX_CHARS.

    Returns:
        The (possibly truncated) source code string.
    """
    if max_chars is None:
        max_chars = DEFAULT_MAX_CHARS

    if len(code) <= max_chars:
        return code

    truncated = code[:max_chars]

    # Try to cut at the last newline so we don't slice mid-line
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars * 0.8:  # only snap if we're not losing too much
        truncated = truncated[:last_newline]

    lines_shown = truncated.count("\n") + 1
    total_lines = code.count("\n") + 1
    omitted = total_lines - lines_shown

    marker = (
        f"\n\n// [NodeGuard] ⚠️  Code truncated for token efficiency.\n"
        f"// Showing {lines_shown} of {total_lines} lines "
        f"({omitted} lines omitted from the end).\n"
        f"// Review findings apply to the visible portion only.\n"
    )

    return truncated + marker


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimate using the heuristic: 1 token ≈ 4 characters.
    Suitable only for logging and debugging — not for billing calculations.
    """
    return max(1, len(text) // 4)
