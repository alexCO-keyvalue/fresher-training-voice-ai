"""LangGraph-powered voice agent.

Uses the tech support graph from graph.py as the LLM backend via
the langchain.LLMAdapter.

Run with: uv run src/langgraph_agent.py dev
"""

import logging

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env.local"))

from livekit.agents import (  # noqa: E402
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
)
from livekit.plugins import langchain  # noqa: E402

from graph import compiled_graph  # noqa: E402

logger = logging.getLogger("langgraph-voice-agent")
logger.setLevel(logging.INFO)


class LangGraphVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful tech support agent for Acme Corp. "
                "You help users with their Acme Dashboard Pro software. "
                "You are also a helpful assistant that can answer questions and help with tasks. "
            )
        )


server = AgentServer()


@server.rtc_session(agent_name="langgraph-agent")
async def entrypoint(ctx: JobContext):
    
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=langchain.LLMAdapter(graph=compiled_graph, stream_mode="custom"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            interruption={"enabled": False},
            preemptive_generation={"enabled": True},
        ),
    )

    await session.start(agent=LangGraphVoiceAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
