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
    stt,
)
from livekit.agents import llm

load_dotenv(find_dotenv(".env.local"))

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

FILLER_PATTERN = re.compile(r"\b(?:um|uh|like|you know|basically|actually)\b", re.IGNORECASE)

TTS_EXPANSIONS = {
    "API": "A P I",
    "URL": "U R L",
    "SQL": "sequel",
    "CLI": "command line",
    "GUI": "gooey",
    "OS": "operating system",
}

MAX_RESPONSE_CHARS = 200

TICKET_DATABASE = {
    "T-1001": {"status": "open", "subject": "Dashboard won't load", "priority": "high"},
    "T-1002": {"status": "resolved", "subject": "Export button missing", "priority": "medium"},
    "T-1003": {"status": "in_progress", "subject": "Slow report generation", "priority": "low"},
}


def extract_ticket_ids(text: str) -> list[str]:
    """Extract ticket IDs like T-1001 from a text string."""
    return re.findall(r"T-\d{4}", text, re.IGNORECASE)


# TODO 1: Implement fetch_user_context() that returns a dict with user profile data.
#   Simulate fetching user data from an API or database. Then update
#   TechSupportAgent.__init__ to accept user_context and inject it into instructions.
#
#   Docs: https://docs.livekit.io/reference/recipes/context_variables/


class TechSupportAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a friendly and knowledgeable tech support agent for a software company called Acme Corp. "
                "You help users troubleshoot issues with their software products.\n\n"
                "# Output rules\n"
                "- Respond in plain text only. Never use markdown, lists, tables, code blocks, or emojis.\n"
                "- Keep replies brief: one to three sentences. Ask one question at a time.\n"
                "- Spell out numbers and abbreviations. Say 'megabytes' not 'MB'.\n\n"
                "# Conversational flow\n"
                "- Start by understanding the user's problem before jumping to solutions.\n"
                "- Walk the user through troubleshooting one step at a time.\n"
                "- Confirm each step is complete before moving to the next.\n"
                "- Summarize what was done when the issue is resolved.\n\n"
                "# Tools\n"
                "- Use lookup_ticket to check the status of a support ticket when the user mentions one.\n"
                "- Use create_ticket to create a new support ticket for the user's issue.\n\n"
                "# Guardrails\n"
                "- Only help with Acme Corp software products.\n"
                "- If the user asks about unrelated topics, politely redirect them.\n"
                "- For billing or account issues, let the user know you can only help with technical problems.\n"
            ),
        )

    async def on_enter(self):
        self.session.generate_reply(
            instructions="Greet the user warmly, introduce yourself as Acme Corp tech support, and ask how you can help today."
        )

    async def stt_node(self, audio, model_settings: ModelSettings):
        async def strip_fillers():
            async for event in Agent.default.stt_node(self, audio, model_settings):
                if isinstance(event, stt.SpeechEvent) and event.alternatives:
                    for alt in event.alternatives:
                        original = alt.text
                        alt.text = FILLER_PATTERN.sub("", alt.text).strip()
                        alt.text = re.sub(r"\s{2,}", " ", alt.text)
                        if original != alt.text:
                            logger.info(f"Filler removed: {original!r} -> {alt.text!r}")
                yield event

        return strip_fillers()

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        async def expand_abbreviations():
            async for chunk in text:
                modified = chunk
                for abbr, expansion in TTS_EXPANSIONS.items():
                    modified = modified.replace(abbr, expansion)
                yield modified

        return Agent.default.tts_node(self, expand_abbreviations(), model_settings)

    async def llm_node(self, chat_ctx: llm.ChatContext, tools: list[llm.Tool], model_settings: ModelSettings):
        char_count = 0

        async def hard_limit():
            nonlocal char_count
            async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
                if isinstance(chunk, llm.ChatChunk) and chunk.delta:
                    content = chunk.delta.content
                    if content:
                        remaining = MAX_RESPONSE_CHARS - char_count
                        if remaining <= 0:
                            logger.info("Hard limit reached, stopping stream.")
                            break
                        if len(content) > remaining:
                            chunk.delta.content = content[:remaining]
                            yield chunk
                            logger.info("Trimmed final chunk and stopped stream.")
                            break
                        char_count += len(content)
                yield chunk

        return hard_limit()

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

    # TODO 2: Override on_user_turn_completed to auto-inject ticket context.
    #   When the user mentions a ticket ID in their message, automatically look
    #   it up and inject the data into the chat context before the LLM responds.
    #
    #   Docs: https://docs.livekit.io/agents/logic/chat-context/


server = AgentServer()


@server.rtc_session(agent_name="voice-agent")
async def entrypoint(ctx: JobContext):
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

    # TODO 3: Register session event handlers.
    #   Use @session.on("event_name") to register handlers for:
    #   "user_input_transcribed", "agent_state_changed", and "error".
    #
    #   Docs: https://docs.livekit.io/reference/agents/events-and-error-handling/

    # TODO 4: Add a shutdown callback to log a session summary.
    #   Use ctx.add_shutdown_callback() to register a cleanup function.
    #
    #   Docs: https://docs.livekit.io/agents/server/lifecycle/

    await session.start(agent=TechSupportAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
