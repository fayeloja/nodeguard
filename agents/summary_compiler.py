from graph.llm import get_llm

def summary_compiler(all_reports: list) -> str:
    llm = get_llm()
    
    combined = "\n\n---\n\n".join(
        [f"FILE: {r['path']}\n\n{r['report']}" for r in all_reports]
    )
    
    prompt = f"""You are a senior engineering lead reviewing a full codebase.
You have received individual code review reports for each file in the repository.

Here are all the reports:

{combined}

Write a concise repository-level summary in this format:

# NodeGuard — Repository Review Summary

## Overall Assessment
[2-3 sentences on the general state of the codebase]

## Repository Severity: [LOW / MEDIUM / HIGH]

## Files Reviewed
[Table with columns: File | Severity | Top Issue]

## Top 5 Cross-Cutting Issues
[Issues that appear across multiple files — patterns, not one-offs]

## Priority Fix Order
[Numbered list — which file to fix first and why]
"""
    response = llm.invoke(prompt)
    return response.content