from graph.llm import get_llm
from graph.state import ReviewState
from utils.token_utils import truncate_code

def code_fixer(state: ReviewState) -> ReviewState:
    llm = get_llm()
    code_snippet = truncate_code(state["code"])

    prompt = f"""You are a senior Node.js engineer.
You have received a code review report flagging HIGH severity issues.
Your job is to rewrite the code fixing ALL identified issues.

ORIGINAL CODE:
```javascript
{code_snippet}
```

LOGIC ISSUES:
{state.get('logic_review', 'None')}

SECURITY ISSUES:
{state.get('security_review', 'None')}

STYLE ISSUES:
{state.get('style_review', 'None')}

Rules:
- Fix every HIGH severity issue identified
- Preserve the original intent and functionality
- Add proper error handling where missing
- Add comments explaining what you changed and why
- Return ONLY the corrected JavaScript code, no explanation outside the code

Return the fixed code inside a javascript code block.
"""
    response = llm.invoke(prompt)
    return {**state, "fixed_code": response.content}