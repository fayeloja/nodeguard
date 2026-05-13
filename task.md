# NodeGuard — Token Optimization & Retry Logic Tasks

## New Files
- `[x]` `utils/cache.py` — content-hash cache with TTL
- `[x]` `utils/token_utils.py` — truncate_code, estimate_tokens
- `[x]` `utils/retry.py` — exponential backoff decorator

## Modified Files
- `[x]` `utils/github_fetcher.py` — max_lines chunking
- `[x]` `agents/logic_analyst.py` — use truncate_code
- `[x]` `agents/security_auditor.py` — use truncate_code
- `[x]` `agents/style_enforcer.py` — use truncate_code
- `[x]` `agents/code_fixer.py` — use truncate_code
- `[x]` `graph/llm.py` — patch invoke with retry wrapper
- `[x]` `main.py` — --no-cache, --batch-size, cache integration

## Verification
- `[x]` Run local file test (first run — cache MISS)
- `[x]` Run local file test (second run — cache HIT)
- `[x]` Run with --no-cache flag
