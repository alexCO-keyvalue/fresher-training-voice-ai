import logging

from dotenv import load_dotenv, find_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import silero

load_dotenv(find_dotenv(".env.local"))

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


class TechSupportAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            # TODO 1: Replace this generic instruction with an Acme Corp tech support
            #   persona prompt. Write it yourself or use ChatGPT to help draft it.
            #   Think about what all a technical support agent would need to think about when
            #   troubleshooting a problem.
            #
            #   There is no single right answer -- make it your own.
            #
            #   Docs: https://docs.livekit.io/agents/start/prompting/
            instructions="You are a helpful voice assistant.",
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="voice-agent")
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=TechSupportAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
