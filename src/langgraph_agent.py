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
        # TODO: Call super().__init__() with instructions for a tech support agent.
        pass

    async def on_enter(self):
        # TODO: Greet the user.
        pass


server = AgentServer()


@server.rtc_session(agent_name="langgraph-agent")
async def entrypoint(ctx: JobContext):
    # TODO: Create a langchain.LLMAdapter wrapping compiled_graph.
    #   Docs: https://docs.livekit.io/agents/integrations/langgraph/
    langgraph_llm = None

    # TODO: Create an AgentSession with STT, LLM (the adapter above), TTS,
    #   and turn_handling configured similarly to previous stages.
    session = None

    # TODO: Start the session and connect to the room.
    pass


if __name__ == "__main__":
    cli.run_app(server)
