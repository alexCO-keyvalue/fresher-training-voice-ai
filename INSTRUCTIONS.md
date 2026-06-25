# Stage 8: LangGraph Integration

## Goal

Replace the built-in LLM with an existing LangGraph workflow as the brain of a voice agent. This is a separate agent from the customer support system you built in stages 1-7.

## Background

In production, your voice agent's "brain" might not be a single LLM call. It might be a complex workflow with classification, tool use, RAG, and routing -- all orchestrated by LangGraph. LiveKit provides an adapter that lets you plug any LangGraph StateGraph in as a drop-in LLM replacement.

The architecture:

```
User speaks
    |
  [STT]  (Deepgram)
    |
  [LangGraph StateGraph]   <-- replaces the direct LLM call
    |   classify -> handle_ticket / handle_knowledge / handle_escalation -> respond
    |
  [TTS]  (Cartesia)
    |
User hears response
```

## What's Provided

- `src/graph.py` -- A complete LangGraph workflow (DO NOT MODIFY). It has:
  - A "classify" node that categorizes the user's intent
  - Three handler nodes: ticket lookup, knowledge base search, escalation
  - A "respond" node that generates the final user-facing response
  - Only the "respond" node produces output the user should hear

- `src/langgraph_agent.py` -- A skeleton voice agent with TODOs. This is the file you edit.

- `src/agent.py` -- Your customer support multi-agent system from stages 1-7. Left untouched.

## Your Tasks

Open `src/langgraph_agent.py` and complete the four TODOs:

1. **TODO 1:** Import `compiled_graph` from `graph.py` and `langchain` from `livekit.plugins`
2. **TODO 2:** Create the adapter: `langchain.LLMAdapter(graph=compiled_graph)`
3. **TODO 3:** Replace `inference.LLM(...)` with the adapter in the AgentSession
4. **TODO 4:** Debug the intermediate output problem -- you'll hear the agent speak internal processing messages. Fix it by adding node filtering.

Run with:
```bash
uv run src/langgraph_agent.py dev
```

## Docs

- [LangGraph + LiveKit example](https://github.com/livekit-examples/python-agents-examples/tree/main/docs/examples/langchain_langgraph)
- [livekit-plugins-langchain on PyPI](https://pypi.org/project/livekit-plugins-langchain/)

## Break It

- Remove the `stream_responses` parameter from the adapter (after you've added it). Talk to the agent and listen -- you'll hear it speak its internal classification and context-gathering outputs. Why is node filtering important?
- Open `src/graph.py` and read the `classify` node. What happens if you ask the agent something completely off-topic?

## Extend It

- Add a new node to `graph.py` that does sentiment analysis on the user's message before routing. If the user seems frustrated, have the "respond" node use an especially empathetic tone.
- Try using the adapter with a RemoteGraph instead of a local compiled graph. What would you need to change?
