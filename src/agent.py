import logging
import re
from typing import AsyncIterable

from dotenv import load_dotenv, find_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    ModelSettings,
    RunContext,
    TurnHandlingOptions,
    cli,
    function_tool,
    inference,
)
from livekit.agents import llm

load_dotenv(find_dotenv(".env.local"))

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

TICKET_DATABASE = {
    "T-1001": {"status": "open", "subject": "Dashboard won't load", "priority": "high"},
    "T-1002": {"status": "resolved", "subject": "Export button missing", "priority": "medium"},
    "T-1003": {"status": "in_progress", "subject": "Slow report generation", "priority": "low"},
}

INVOICE_DATABASE = {
    "INV-2001": {"amount": "$49.99", "date": "May 1, 2026", "status": "paid"},
    "INV-2002": {"amount": "$49.99", "date": "June 1, 2026", "status": "pending"},
}


def fetch_user_context() -> dict:
    """Simulate fetching user profile from a database or API."""
    return {
        "name": "Alex",
        "account_type": "Premium",
        "product": "Acme Dashboard Pro",
        "open_tickets": 2,
    }


# ---------------------------------------------------------------------------
# Triage Agent -- the front door (EXAMPLE: study this pattern)
# ---------------------------------------------------------------------------

class TriageAgent(Agent):
    """Routes the user to the right specialist. This agent is fully implemented
    as an example of the handoff pattern -- study how it passes user_context
    and uses session.update_agent() to transfer to other agents."""

    def __init__(self, user_context: dict) -> None:
        self.user_context = user_context
        super().__init__(
            instructions=(
                "You are the front-desk triage agent at Acme Corp support. "
                "Your job is to understand the user's issue and route them to the right specialist.\n\n"
                f"The user's name is {user_context['name']} and they are a {user_context['account_type']} member.\n\n"
                "# Routing rules\n"
                "- For technical issues (bugs, errors, setup, performance): transfer to the technical agent.\n"
                "- For billing, invoices, payments, or subscription questions: transfer to the billing agent.\n"
                "- If unclear, ask one clarifying question before transferring.\n\n"
                "# Output rules\n"
                "- Respond in plain text only. No markdown, lists, or emojis.\n"
                "- Keep replies brief: one to two sentences.\n"
            ),
        )

    async def on_enter(self):
        self.session.generate_reply(
            instructions=(
                f"Greet {self.user_context['name']} by name and say you're the Acme Corp support triage. "
                "Ask what kind of help they need today: technical or billing."
            )
        )

    @function_tool
    async def transfer_to_technical(self, context: RunContext):
        """Transfer the user to the technical support agent. Use when the user
        has a technical issue like a bug, error, setup, or performance problem."""
        logger.info("Transferring to TechnicalAgent")
        self.session.update_agent(TechnicalAgent(self.user_context))

    @function_tool
    async def transfer_to_billing(self, context: RunContext):
        """Transfer the user to the billing support agent. Use when the user
        has a billing, invoice, payment, or subscription question."""
        logger.info("Transferring to BillingAgent")
        self.session.update_agent(BillingAgent(self.user_context))


# ---------------------------------------------------------------------------
# Technical Agent -- handles bugs, errors, troubleshooting (EXAMPLE)
# ---------------------------------------------------------------------------

class TechnicalAgent(Agent):
    """Handles technical support. Also fully implemented as an example.
    Note how it accepts user_context and has a transfer_to_triage tool
    to hand back to the triage agent."""

    def __init__(self, user_context: dict) -> None:
        self.user_context = user_context
        super().__init__(
            instructions=(
                "You are the technical support specialist at Acme Corp. "
                "You help users troubleshoot software bugs, errors, setup issues, and performance problems.\n\n"
                f"The user's name is {user_context['name']} ({user_context['account_type']} account), "
                f"using {user_context['product']}.\n\n"
                "# Conversational flow\n"
                "- Understand the problem first, then troubleshoot step by step.\n"
                "- Confirm each step before moving on.\n"
                "- Summarize the resolution when done.\n\n"
                "# Tools\n"
                "- Use lookup_ticket to check ticket status when the user mentions a ticket.\n"
                "- Use create_ticket to create a new ticket for the user's issue.\n"
                "- Use transfer_to_triage to send the user back if they need billing help.\n\n"
                "# Output rules\n"
                "- Respond in plain text only. No markdown, lists, or emojis.\n"
                "- Keep replies brief: one to three sentences.\n"
                "- Spell out abbreviations.\n"
            ),
        )

    async def on_enter(self):
        self.session.generate_reply(
            instructions=(
                f"Introduce yourself to {self.user_context['name']} as the Acme Corp technical support specialist. "
                "Let them know you're here to help with their technical issue and ask them to describe the problem."
            )
        )

    @function_tool
    async def lookup_ticket(self, context: RunContext, ticket_id: str):
        """Look up the status of a support ticket by its ID (e.g. T-1001).

        Args:
            ticket_id: The ticket ID to look up, such as T-1001.
        """
        logger.info(f"Tool: lookup_ticket({ticket_id})")
        ticket = TICKET_DATABASE.get(ticket_id.upper())
        if not ticket:
            return f"No ticket found with ID {ticket_id}."
        return (
            f"Ticket {ticket_id}: subject is '{ticket['subject']}', "
            f"status is {ticket['status']}, priority is {ticket['priority']}."
        )

    @function_tool
    async def create_ticket(self, context: RunContext, subject: str):
        """Create a new support ticket for the user's issue.

        Args:
            subject: A brief description of the issue to create a ticket for.
        """
        ticket_num = 1001 + len(TICKET_DATABASE)
        ticket_id = f"T-{ticket_num}"
        TICKET_DATABASE[ticket_id] = {
            "status": "open",
            "subject": subject,
            "priority": "medium",
        }
        logger.info(f"Tool: create_ticket({ticket_id}, '{subject}')")
        return f"Ticket {ticket_id} created with subject '{subject}'. Status is open, priority is medium."

    @function_tool
    async def transfer_to_triage(self, context: RunContext):
        """Transfer the user back to triage. Use when the user needs help
        with a non-technical issue like billing."""
        logger.info("Transferring back to TriageAgent")
        self.session.update_agent(TriageAgent(self.user_context))


# ---------------------------------------------------------------------------
# Billing Agent -- handles invoices, payments, subscriptions
# ---------------------------------------------------------------------------
#
# TODO 1: Build BillingAgent from scratch.
#   Study TriageAgent and TechnicalAgent above as examples of the pattern.
#   Your BillingAgent should handle invoice lookups and be able to transfer
#   back to triage. Use INVOICE_DATABASE for data.
#
#   Docs: https://docs.livekit.io/agents/logic/turns/agents-and-handoffs/

class BillingAgent(Agent):
    pass  # Replace this with your implementation


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

server = AgentServer()


@server.rtc_session(agent_name="voice-agent")
async def entrypoint(ctx: JobContext):
    user_context = fetch_user_context()
    logger.info(f"User context loaded: {user_context}")

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            interruption={"enabled": False},
            preemptive_generation={"enabled": True},
        ),
    )

    await session.start(agent=TriageAgent(user_context=user_context), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
