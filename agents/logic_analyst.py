from graph.llm import get_llm
from graph.state import ReviewState
from utils.token_utils import truncate_code

def logic_analyst(state: ReviewState) -> ReviewState:
    llm = get_llm()
    code_snippet = truncate_code(state["code"])

    prompt = f"""You are a senior Node.js engineer specializing in code correctness.

Review the following JavaScript/Node.js code for logic issues only.

Check for:
- Bugs and incorrect logic
- Edge cases not handled
- Incorrect use of async/await or promises
- Off-by-one errors, null/undefined risks
- Wrong assumptions about inputs

Code to review:
```javascript
{code_snippet}
```

Respond in this exact format:
LOGIC REVIEW
============
[Your findings here. Be specific, reference line behaviour where possible.]

SEVERITY: [LOW / MEDIUM / HIGH]
"""
    response = llm.invoke(prompt)
    return {**state, "logic_review": response.content}