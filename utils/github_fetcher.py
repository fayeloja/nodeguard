import os
import requests
from typing import List, Dict

# Maximum number of lines to keep from any single file.
# Files exceeding this limit are truncated and annotated.
DEFAULT_MAX_LINES = int(os.getenv("NODEGUARD_MAX_FILE_LINES", "300"))


def _get_headers() -> dict:
    """Return auth headers if GITHUB_TOKEN is set, otherwise empty dict."""
    token = os.getenv("GITHUB_TOKEN", "")
    return {"Authorization": f"token {token}"} if token else {}


def _truncate_lines(content: str, path: str, max_lines: int) -> str:
    """
    Return *content* limited to *max_lines* lines.
    If truncated, a header comment is prepended so the LLM knows it's
    seeing a representative slice.
    """
    lines = content.splitlines()
    if len(lines) <= max_lines:
        return content

    kept = lines[:max_lines]
    omitted = len(lines) - max_lines
    header = (
        f"// [NodeGuard] File truncated for token efficiency.\n"
        f"// Showing first {max_lines} of {len(lines)} lines "
        f"({omitted} lines omitted) from: {path}\n\n"
    )
    return header + "\n".join(kept)


def get_js_files_from_repo(
    repo_url: str,
    max_lines: int = DEFAULT_MAX_LINES,
) -> List[Dict[str, str]]:
    """
    Takes a GitHub repo URL and returns a list of dicts:
    [{ "path": "src/index.js", "content": "..." }, ...]

    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/tree/main/subfolder

    Args:
        repo_url:  Public (or authenticated) GitHub repository URL.
        max_lines: Maximum source lines to keep per file. Files exceeding
                   this are truncated with an explanatory header comment.
    """
    headers = _get_headers()

    # Parse owner and repo from URL
    parts = repo_url.rstrip("/").replace("https://github.com/", "").split("/")
    owner = parts[0]
    repo = parts[1]

    # Determine subfolder if URL points to one
    subfolder = ""
    if len(parts) > 4 and parts[2] == "tree":
        # parts[3] is the branch, parts[4:] is the path
        subfolder = "/".join(parts[4:])

    print(f"\n📦 Fetching repo: {owner}/{repo}")
    if subfolder:
        print(f"📁 Subfolder: {subfolder}")

    # Use GitHub API to get file tree
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} — {response.json().get('message')}")

    tree = response.json().get("tree", [])

    # Filter for .js files only (excluding node_modules, dist, build)
    EXCLUDED = ["node_modules", "dist", "build", ".min.js", "vendor"]

    js_files = [
        item for item in tree
        if item["type"] == "blob"
        and item["path"].endswith(".js")
        and not any(ex in item["path"] for ex in EXCLUDED)
        and (item["path"].startswith(subfolder) if subfolder else True)
    ]

    if not js_files:
        raise Exception("No .js files found in this repository.")

    print(f"📄 Found {len(js_files)} JavaScript file(s)\n")

    # Fetch content of each file via raw GitHub URL
    results = []
    for item in js_files:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{item['path']}"
        file_response = requests.get(raw_url, headers=headers)

        if file_response.status_code == 200:
            content = file_response.text
            # Skip very small files (likely config/empty)
            if len(content.strip()) > 100:
                # Apply line-level chunking before storing
                chunked = _truncate_lines(content, item["path"], max_lines)
                was_truncated = len(content.splitlines()) > max_lines
                results.append({
                    "path": item["path"],
                    "content": chunked,
                    "truncated": was_truncated,
                })
                suffix = " [truncated]" if was_truncated else ""
                print(f"  ✅ {item['path']}{suffix}")
            else:
                print(f"  ⏭️  Skipped (too small): {item['path']}")
        else:
            print(f"  ❌ Failed to fetch: {item['path']}")

    return results