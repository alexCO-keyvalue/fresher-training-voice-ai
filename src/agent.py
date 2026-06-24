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

    # TODO 1: Implement the lookup_ticket tool.
    #   Create a @function_tool method that looks up a ticket by its ID
    #   from the TICKET_DATABASE dict above.
    #
    #   Docs: https://docs.livekit.io/agents/logic/tools/definition/

    # TODO 2 (Build from scratch): Create a create_ticket tool.
    #   Design and implement a tool that creates a new ticket in TICKET_DATABASE.
    #   No skeleton is provided -- figure out the decorator, method signature,
    #   docstring, and return value yourself.
    #
    #   Docs: https://docs.livekit.io/agents/logic/tools/definition/


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

    await session.start(agent=TechSupportAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
