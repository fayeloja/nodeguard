from typing import TypedDict, Optional

class ReviewState(TypedDict):
    code: str                          # the Node.js code being reviewed
    logic_review: Optional[str]        # output from Logic Analyst
    security_review: Optional[str]     # output from Security Auditor
    style_review: Optional[str]        # output from Style Enforcer
    final_report: Optional[str]        # output from Report Compiler
    fixed_code: Optional[str]          # output from Code Fixer