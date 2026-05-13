# NodeGuard: Token Optimization & Retry Logic

Improve `main.py` and the agent pipeline to reduce token consumption and handle API rate limits gracefully.

## Proposed Changes

### 1 · Token Optimization

#### [NEW] `utils/cache.py`
A file-based cache keyed by the SHA-256 hash of a file's content. Before invoking the full 4-agent LLM pipeline, `main.py` checks whether a result already exists for that exact content hash. Cache entries are stored as JSON in a `.nodeguard_cache/` directory and include a configurable TTL (default 24 h). This means **unchanged files are never re-analysed**.

#### [MODIFY] `utils/github_fetcher.py`
Add a `max_lines` parameter (default **300 lines**). Files larger than `max_lines` are chunked: only the first N lines are sent to the LLM, with a header noting that the review covers a representative slice. This prevents sending thousands of tokens for a single huge file.

#### [MODIFY] `agents/logic_analyst.py`, `security_auditor.py`, `style_enforcer.py`
Replace the raw `{state['code']}` injection with a call to a shared `truncate_code(code, max_chars=4000)` utility. This caps the code context sent in each prompt at ~4 000 characters (≈ 1 000 tokens), which is usually enough for the LLM to spot issues while keeping costs low.

#### [NEW] `utils/token_utils.py`
- `truncate_code(code, max_chars)` — trims code with a clear `[... truncated ...]` marker so the LLM knows context was cut.
- `estimate_tokens(text)` — rough token counter (chars / 4) for debug logging.

#### [MODIFY] `main.py`
- Add `--no-cache` CLI flag to bypass the cache when needed.
- Add `--batch-size N` CLI flag (default **5**). Files are processed N at a time with a short sleep between batches — this naturally reduces burst API pressure.
- Log estimated token savings when a cached result is reused.

---

### 2 · Retry Logic with Exponential Backoff

#### [NEW] `utils/retry.py`
A decorator `with_retry(max_attempts=5, base_delay=1.0, max_delay=60.0)` that:
- Catches `RateLimitError` / `APIStatusError` from both `langchain-groq` and `langchain-openai`.
- Waits `base_delay * 2^attempt + jitter` seconds between retries (full jitter strategy).
- Logs each retry attempt with the wait time using `rich`.
- Re-raises the error after all attempts are exhausted.

#### [MODIFY] `graph/llm.py`
Wrap every `llm.invoke(prompt)` call by applying the `@with_retry` decorator at the `get_llm()` return point — specifically, monkey-patch the `invoke` method on the returned LLM instance so all agents benefit without touching each agent file.

> [!NOTE]
> Alternatively we can wrap at the agent level. Patching the LLM instance in `get_llm()` is cleaner since it's a single place and automatically covers future agents.

---

## File Change Summary

| File | Action | Why |
|---|---|---|
| `utils/cache.py` | **NEW** | Content-hash cache with TTL |
| `utils/token_utils.py` | **NEW** | `truncate_code`, `estimate_tokens` |
| `utils/retry.py` | **NEW** | Exponential backoff decorator |
| `utils/github_fetcher.py` | MODIFY | Add `max_lines` chunking |
| `agents/logic_analyst.py` | MODIFY | Use `truncate_code` |
| `agents/security_auditor.py` | MODIFY | Use `truncate_code` |
| `agents/style_enforcer.py` | MODIFY | Use `truncate_code` |
| `agents/code_fixer.py` | MODIFY | Use `truncate_code` |
| `graph/llm.py` | MODIFY | Patch `invoke` with retry wrapper |
| `main.py` | MODIFY | `--no-cache`, `--batch-size`, cache integration |
| `requirements.txt` | MODIFY | No new deps needed (stdlib only) |

## Verification Plan

### Automated
```
python main.py samples/sample.js --verbose           # local file — should pass
python main.py samples/sample.js --verbose           # second run — should show cache HIT
python main.py samples/sample.js --no-cache          # force fresh analysis
```

### Manual
- Trigger a rate-limit scenario by using an invalid key and confirm retries are logged with increasing delays.
- Run against a GitHub repo with `--batch-size 2` and confirm files are processed in groups with inter-batch pauses.
