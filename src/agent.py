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
    TurnHandlingOptions,
    cli,
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

    # TODO 1: Override stt_node to strip filler words from the user's speech.
    #   The FILLER_PATTERN regex above matches common fillers like "um", "uh", "like".
    #   Override stt_node to intercept SpeechEvent objects from
    #   Agent.default.stt_node() and remove filler words from the transcript
    #   text in each alternative.
    #
    #   Docs: https://docs.livekit.io/agents/build/nodes/#stt-node

    # TODO 2: Override tts_node to expand abbreviations for correct TTS pronunciation.
    #   The TTS_EXPANSIONS dict maps abbreviations to how they should be spoken.
    #   For example, "API" should become "A P I" so the TTS doesn't say "appy".
    #
    #   Docs: https://docs.livekit.io/agents/build/nodes/#tts_node

    # TODO 3: Override llm_node to enforce a hard character limit on responses.
    #   Use MAX_RESPONSE_CHARS to cap the total characters the LLM can output.
    #   Stream ChatChunk objects from Agent.default.llm_node() and track the
    #   character count. Trim the final chunk if it exceeds the limit.
    #
    #   Docs: https://docs.livekit.io/agents/build/nodes/#llm-node


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
