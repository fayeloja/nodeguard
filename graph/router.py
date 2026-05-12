from graph.state import ReviewState

def severity_router(state: ReviewState) -> str:
    """
    Reads the final report and routes to code_fixer if HIGH severity,
    or ends the pipeline if LOW/MEDIUM.
    """
    report = state.get("final_report", "")
    
    if "Overall Severity: HIGH" in report:
        print("\n⚠️  HIGH severity detected — routing to auto-fix agent...\n")
        return "code_fixer"
    else:
        print("\n✅ Severity acceptable — no auto-fix needed.\n")
        return END_SIGNAL

END_SIGNAL = "__end__"