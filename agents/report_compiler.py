# pyrefly: ignore [missing-import]
from graph.llm import get_llm
from graph.state import ReviewState

def report_compiler(state: ReviewState) -> ReviewState:
    llm = get_llm()
    
    prompt = f"""You are a senior engineering lead. 
You have received three independent reviews of a piece of Node.js code.
Your job is to compile them into a single, clear, actionable report.

LOGIC REVIEW:
{state.get('logic_review', 'None')}

SECURITY REVIEW:
{state.get('security_review', 'None')}

STYLE REVIEW:
{state.get('style_review', 'None')}

Write a final report in this exact format:

# NodeGuard Code Review Report

## Summary
[2-3 sentence overall assessment of the code]

## Critical Issues
[List only HIGH severity issues across all reviews. If none, write "None found."]

## Recommendations
[Numbered list of the most important things to fix, in priority order]

## Full Findings
### Logic
[Paste logic review findings]

### Security
[Paste security review findings]

### Style
[Paste style review findings]

## Overall Severity: [LOW / MEDIUM / HIGH]
"""
    response = llm.invoke(prompt)
    return {**state, "final_report": response.content}