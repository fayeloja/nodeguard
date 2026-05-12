# pyrefly: ignore [missing-import]
from graph.llm import get_llm
from graph.state import ReviewState

def style_enforcer(state: ReviewState) -> ReviewState:
    llm = get_llm()
    
    prompt = f"""You are a senior Node.js engineer focused on code quality and maintainability.

Review the following JavaScript/Node.js code for style and quality issues only.

Check for:
- Poor naming conventions (variables, functions, files)
- Functions doing too many things (violates single responsibility)
- Unnecessary complexity or deeply nested code
- Missing or poor error handling patterns
- Lack of modularity or reusability
- Node.js/JavaScript best practices violations

Code to review:
```javascript
{state['code']}
```

Respond in this exact format:
STYLE REVIEW
============
[Your findings here. Be constructive and specific.]

SEVERITY: [LOW / MEDIUM / HIGH]
"""
    response = llm.invoke(prompt)
    return {**state, "style_review": response.content}