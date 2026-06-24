import logging

from dotenv import load_dotenv, find_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
)

load_dotenv(find_dotenv(".env.local"))

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


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

        # TODO 1: Disable interruptions so the user cannot cut off the agent mid-sentence.
        #   By default, interruptions are enabled.
        #
        #   Docs: https://docs.livekit.io/reference/agents/turn-handling-options/#interruptionoptions

        # TODO 2: Add a turn detector using inference.TurnDetector().
        #   Without a turn detector, the agent relies only on VAD silence duration to decide
        #   when you're done talking.
        #
        #   Docs: https://docs.livekit.io/agents/logic/turns/turn-detector/

        # TODO 3: Enable preemptive generation.
        #   When enabled, the LLM starts generating a response while the turn detector
        #   is still deciding if you're done speaking. If you keep talking, the partial
        #   response is discarded. This reduces perceived latency.
        #   Docs: https://docs.livekit.io/agents/logic/turns/tuning/
    )

    await session.start(agent=TechSupportAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
