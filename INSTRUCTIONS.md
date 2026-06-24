# Stage 6: Context, Events, and Session Lifecycle

## Goal

Learn how to inject runtime data into the agent, react to session events, and use the ChatContext hook to enrich conversations with external data.

## Background

So far, the agent's knowledge is limited to its static instructions and tool calls. In production, you often need to:

- **Inject user context** -- greet the user by name, know their account type, personalize the experience
- **React to events** -- log transcripts, track state changes, handle errors gracefully
- **Enrich the chat context** -- automatically provide relevant data to the LLM based on what the user says

LiveKit provides hooks for all of these:
- `fetch_user_context()` + f-string instructions for personalization
- `on_user_turn_completed()` for injecting data into the ChatContext before the LLM responds
- `session.on("event_name")` for reacting to session events
- `ctx.add_shutdown_callback()` for cleanup when the session ends

## Your Tasks

Open `src/agent.py` and complete the four TODOs:

1. **TODO 1:** Implement `fetch_user_context()` and inject the data into agent instructions via f-strings
2. **TODO 2:** Override `on_user_turn_completed` to auto-inject ticket data when the user mentions a ticket ID
3. **TODO 3:** Register session event handlers for `user_input_transcribed`, `agent_state_changed`, and `error`
4. **TODO 4:** Add a shutdown callback to log a session summary

## Docs

- [Context variables recipe](https://docs.livekit.io/reference/recipes/context_variables/)
- [Chat context](https://docs.livekit.io/agents/logic/chat-context/)
- [Events and error handling](https://docs.livekit.io/reference/agents/events-and-error-handling/)
- [Job lifecycle](https://docs.livekit.io/agents/server/lifecycle/)

## Break It

- Hardcode a wrong name in the instructions (e.g. "The user's name is Bob"). Talk to the agent -- does it call you Bob?
- Remove `on_user_turn_completed` and mention ticket T-1001 in conversation. Does the agent know about the ticket without using the lookup tool?

## Extend It

- Use `ctx.wait_for_participant()` to get the real participant identity and attributes from the LiveKit room instead of the fake `fetch_user_context()`. Pass `participant.attributes.get('language', 'en')` to configure the STT language dynamically.
