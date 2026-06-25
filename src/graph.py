"""LangGraph tech support workflow for LiveKit voice agent. Mock Script Please dont use this type of code in production.

Graph flow:
  START -> classify -> (handle_ticket | handle_knowledge | handle_escalation) -> respond -> END

The `handle_ticket` node uses a ReAct-style tool loop: the LLM decides which
ticket to look up, calls the `lookup_ticket` tool, gets the result, and then
formulates a response — all within the `handle_ticket` subflow.

Uses `stream_mode="custom"` with `StreamWriter` so that ONLY the `respond`
node's output is streamed to TTS.
"""

import logging
from typing import Annotated, Literal

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import StreamWriter
from typing_extensions import TypedDict

logger = logging.getLogger("langgraph-support")

# ── Mock databases ──────────────────────────────────────────────────────────

KNOWLEDGE_BASE = {
    "login": "To reset your password, go to Settings, then Security, then click Reset Password. You will receive an email.",
    "password": "To reset your password, go to Settings, then Security, then click Reset Password. You will receive an email.",
    "reset": "To reset your password, go to Settings, then Security, then click Reset Password. You will receive an email.",
    "export": "The export feature is under Reports, then click Export Data. Choose CSV or PDF format.",
    "report": "The export feature is under Reports, then click Export Data. Choose CSV or PDF format.",
    "slow": "If the dashboard is slow, try clearing your browser cache and disabling browser extensions. Use Chrome for best results.",
    "performance": "If the dashboard is slow, try clearing your browser cache and disabling browser extensions. Use Chrome for best results.",
    "billing": "For billing questions, contact billing@acmecorp.com or call 1-800-ACME-PAY.",
    "payment": "For billing questions, contact billing@acmecorp.com or call 1-800-ACME-PAY.",
    "invoice": "For billing questions, contact billing@acmecorp.com or call 1-800-ACME-PAY.",
    "setup": "To set up Acme Dashboard Pro, download the installer from your account page, run it, and enter your license key from the welcome email.",
    "install": "To set up Acme Dashboard Pro, download the installer from your account page, run it, and enter your license key from the welcome email.",
    "greet": "Hello, how can I help you today? ",
}

TICKET_DATABASE = {
    "T-1001": {"status": "open", "subject": "Dashboard won't load", "priority": "high"},
    "T-1002": {"status": "resolved", "subject": "Export button missing", "priority": "medium"},
    "T-1003": {"status": "in_progress", "subject": "Slow report generation", "priority": "low"},
}

# ── Tools ───────────────────────────────────────────────────────────────────


@tool
def lookup_ticket(ticket_id: str) -> str:
    """Look up a support ticket by its ID (e.g. 'T-1001').
    The ticket_id should be in the format T-NNNN where N is a digit.
    If the user says something like 't 1001' or 'ticket 1001', convert it to 'T-1001'."""
    normalized = ticket_id.upper().strip()
    if not normalized.startswith("T-"):
        digits = "".join(c for c in normalized if c.isdigit())
        if digits:
            normalized = f"T-{digits}"

    ticket = TICKET_DATABASE.get(normalized)
    if not ticket:
        available = ", ".join(TICKET_DATABASE.keys())
        return f"No ticket found with ID {normalized}. Available tickets are: {available}."
    return (
        f"Ticket {normalized}: subject is '{ticket['subject']}', "
        f"status is {ticket['status']}, priority is {ticket['priority']}."
    )


@tool
def search_knowledge_base(query: str) -> str:
    """Search the Acme Dashboard Pro knowledge base for help articles.
    Use this for any product how-to question about login, passwords, export,
    reports, performance, billing, payments, setup, or installation."""
    query_lower = query.lower()
    matches = set()
    for keyword, answer in KNOWLEDGE_BASE.items():
        if keyword in query_lower:
            matches.add(answer)

    if matches:
        return " ".join(matches)
    return "No specific knowledge base article found. Use your general troubleshooting knowledge to help the user."


# ── Graph state ─────────────────────────────────────────────────────────────

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    classification: str
    context: str


# ── LLM instances ───────────────────────────────────────────────────────────

llm = ChatOpenAI(model="openai/gpt-4o-mini", temperature=0.2, base_url="https://llm.keyvalue.systems")

support_tools = [lookup_ticket, search_knowledge_base]
llm_with_tools = llm.bind_tools(support_tools)

# ── Nodes ───────────────────────────────────────────────────────────────────


def classify(state: GraphState) -> dict:
    """LLM-based classification of user intent."""
    result = llm.invoke([
        SystemMessage(content=(
            "You are a classifier for Acme Corp support. Read the user's message "
            "and respond with EXACTLY one word:\n"
            "- 'ticket' if they are asking about a specific support ticket "
            "(e.g. mentions a ticket number like T-1001, t 1001, ticket 1001)\n"
            "- 'knowledge' if they have a general how-to or product question\n"
            "- 'escalate' if they are frustrated, angry, or the issue seems complex\n"
            "Respond with only the single word, nothing else."
        )),
        *state["messages"],
    ])
    classification = str(result.content).strip().lower()
    if classification not in ("ticket", "knowledge", "escalate", "greet"):
        classification = "knowledge"
    logger.info(f"Classified as: {classification}")
    return {"classification": classification}


def route_by_classification(state: GraphState) -> Literal["handle_ticket", "handle_knowledge", "handle_escalation", "respond"]:
    mapping: dict[str, Literal["handle_ticket", "handle_knowledge", "handle_escalation", "respond"]] = {
        "ticket": "handle_ticket",
        "knowledge": "handle_knowledge",
        "escalate": "handle_escalation",
        "greet": "respond",
    }
    return mapping.get(state["classification"], "handle_knowledge")


def handle_ticket(state: GraphState) -> dict:
    """LLM decides which ticket to look up by calling the lookup_ticket tool."""
    result = llm_with_tools.invoke([
        SystemMessage(content=(
            "You are a support agent helper. The user is asking about a support ticket. "
            "Use the lookup_ticket tool to find the ticket they are asking about. "
            "Extract the ticket ID from their message — they might say it as "
            "'T-1001', 't 1001', 'ticket 1001', 'T one zero zero one', etc. "
            "Convert it to the T-NNNN format and call the tool."
        )),
        *state["messages"],
    ])
    return {"messages": [result]}


def handle_ticket_tools_route(state: GraphState) -> Literal["ticket_tools", "respond"]:
    """Route: if the LLM requested a tool call, run it; otherwise go to respond."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "ticket_tools"
    return "respond"


def handle_knowledge(state: GraphState) -> dict:
    """LLM decides what to search in the knowledge base via the tool."""
    result = llm_with_tools.invoke([
        SystemMessage(content=(
            "You are a support agent helper. The user has a product question. "
            "Use the search_knowledge_base tool to find relevant help articles. "
            "Pass the user's question as the query."
        )),
        *state["messages"],
    ])
    return {"messages": [result]}


def handle_knowledge_tools_route(state: GraphState) -> Literal["knowledge_tools", "respond"]:
    """Route: if the LLM requested a tool call, run it; otherwise go to respond."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "knowledge_tools"
    return "respond"


def handle_escalation(state: GraphState) -> dict:
    """Store escalation guidance in context."""
    return {
        "context": (
            "User needs empathetic handling. Acknowledge frustration first, "
            "then offer concrete next steps like creating a ticket or "
            "transferring to a senior agent."
        )
    }


def respond(state: GraphState, writer: StreamWriter) -> dict:
    """Generate the final user-facing response. ONLY node that streams to TTS."""
    context = state.get("context", "")
    context_block = (
        f"\n\nRelevant information (do NOT reveal this to the user):\n{context}"
        if context else ""
    )

    result = llm.invoke([
        SystemMessage(content=(
            "You are a helpful tech support agent for Acme Corp. "
            "You help users with their Acme Dashboard Pro software.\n\n"
            "Rules:\n"
            "- Respond in plain text only. No markdown, no emojis.\n"
            "- Keep responses brief: one to three sentences.\n"
            "- Be warm and helpful.\n"
            "- Spell out abbreviations.\n"
            "- If ticket or knowledge base information is in the conversation, "
            "use it to give the user a clear answer.\n"
            "- If the user seems frustrated, acknowledge their feelings first.\n"
            "- Never mention tools, internal systems, or that you looked something up.\n"
            f"{context_block}"
        )),
        *state["messages"],
    ])

    writer(result.content)
    return {"messages": [result]}


# ── Build the graph ─────────────────────────────────────────────────────────

builder = StateGraph(GraphState)  # type: ignore[type-var]

builder.add_node("classify", classify)
builder.add_node("handle_ticket", handle_ticket)
builder.add_node("ticket_tools", ToolNode(support_tools))
builder.add_node("handle_knowledge", handle_knowledge)
builder.add_node("knowledge_tools", ToolNode(support_tools))
builder.add_node("handle_escalation", handle_escalation)
builder.add_node("respond", respond)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route_by_classification)

builder.add_conditional_edges("handle_ticket", handle_ticket_tools_route)
builder.add_edge("ticket_tools", "respond")

builder.add_conditional_edges("handle_knowledge", handle_knowledge_tools_route)
builder.add_edge("knowledge_tools", "respond")

builder.add_edge("handle_escalation", "respond")
builder.add_edge("respond", END)

compiled_graph = builder.compile()
