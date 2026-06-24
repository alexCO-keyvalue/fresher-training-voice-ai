# Stage 5: Function Tools

## Goal

Give the agent the ability to take actions -- not just talk. Tools let the LLM call Python functions to look up data, create records, or trigger side effects.

## Background

Without tools, the agent can only respond based on what's in its instructions and the conversation history. With `@function_tool`, you can give the LLM access to Python functions. The LLM decides when to call them based on the tool's **docstring** -- this is how it learns what the tool does and when to use it.

The flow when a tool is called:
1. User says something like "Can you check ticket T-1001?"
2. The LLM reads the tool's docstring and decides to call `lookup_ticket(ticket_id="T-1001")`
3. Your Python function runs and returns a result string
4. The LLM incorporates the result into its response
5. The response is spoken to the user via TTS

## Your Tasks

Open `src/agent.py` and implement the two tools:

1. **TODO 1:** Implement `lookup_ticket` -- look up a ticket by ID from `TICKET_DATABASE` and return a formatted string. The decorator, signature, and hints are provided.
2. **TODO 2:** Build `create_ticket` from scratch -- no skeleton provided. You need to figure out the decorator, method signature, docstring, and return value yourself.

## Docs

- [Function tools](https://docs.livekit.io/agents/logic/tools/definition/)

## Break It

- Make `lookup_ticket` return a Python dict instead of a string. What does the agent say?
- Now make it return `None`. What happens?
- Remove the docstring from `lookup_ticket` entirely. Ask the agent to look up a ticket. Does it still work?

## Extend It

- Add an `update_ticket_status` tool that can change a ticket's status. Give it validation -- it should only accept "open", "in_progress", and "resolved" as valid statuses, and return an error message for anything else.
