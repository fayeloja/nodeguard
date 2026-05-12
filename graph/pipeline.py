from langgraph.graph import StateGraph, END
from graph.state import ReviewState
from graph.router import severity_router, END_SIGNAL
from agents.logic_analyst import logic_analyst
from agents.security_auditor import security_auditor
from agents.style_enforcer import style_enforcer
from agents.report_compiler import report_compiler
from agents.code_fixer import code_fixer

def build_pipeline():
    graph = StateGraph(ReviewState)

    # Register nodes
    graph.add_node("logic_analyst", logic_analyst)
    graph.add_node("security_auditor", security_auditor)
    graph.add_node("style_enforcer", style_enforcer)
    graph.add_node("report_compiler", report_compiler)
    graph.add_node("code_fixer", code_fixer)

    # Sequential chain
    graph.set_entry_point("logic_analyst")
    graph.add_edge("logic_analyst", "security_auditor")
    graph.add_edge("security_auditor", "style_enforcer")
    graph.add_edge("style_enforcer", "report_compiler")

    # Conditional edge — this is the new part
    graph.add_conditional_edges(
        "report_compiler",          # from this node
        severity_router,            # call this function to decide
        {
            "code_fixer": "code_fixer",   # if returns "code_fixer" → go there
            END_SIGNAL: END               # if returns "__end__" → stop
        }
    )

    graph.add_edge("code_fixer", END)

    return graph.compile()