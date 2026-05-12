# pyrefly: ignore [missing-import]
from graph.llm import get_llm
from graph.state import ReviewState

def security_auditor(state: ReviewState) -> ReviewState:
    llm = get_llm()
    
    prompt = f"""You are a security engineer specializing in Node.js application security.

Review the following JavaScript/Node.js code for security vulnerabilities only.

Check for:
- Injection risks (SQL, NoSQL, command injection)
- Improper input validation or sanitization
- Hardcoded secrets or credentials
- Insecure use of dependencies or APIs
- Authentication or authorization flaws
- Sensitive data exposure

Code to review:
```javascript
{state['code']}
```

Previous findings for context:
{state.get('logic_review', 'None')}

Respond in this exact format:
SECURITY REVIEW
===============
[Your findings here. Be specific about the vulnerability and its risk.]

SEVERITY: [LOW / MEDIUM / HIGH]
"""
    response = llm.invoke(prompt)
    return {**state, "security_review": response.content}