# Stage 2: Prompt Engineering

## Goal

Learn how voice-specific prompts differ from chat prompts. Craft a persona prompt that sounds natural when spoken aloud.

## Background

The `instructions` string you pass to an Agent becomes the system prompt for the LLM. But unlike a chatbot, the LLM's output will be **spoken aloud** by the TTS engine. 

Voice prompts need to guide the LLM to produce **conversational output** that sounds natural when spoken.

## Your Task

Open `src/agent.py` and find the TODO comment inside `TechSupportAgent.__init__`. Replace the generic one-liner with a proper Acme Corp tech support persona prompt.

Use ChatGPT to help draft it, or write it freehand. There is no single correct answer.

## Docs

- [Prompting guide](https://docs.livekit.io/agents/start/prompting/)

## Break It

- Write instructions that use markdown formatting (bullet points, bold text, headers). Talk to the agent. What does the TTS sound like when it tries to speak "asterisk asterisk important asterisk asterisk"?
- Write a very long, verbose prompt (500+ words). Does the agent become slower to respond? Why?

## Extend It (Extra Exercise)

Right now, the agent waits silently until you speak first. Figure out how to make the agent **start the conversation** -- greet the user proactively in a lively tone without waiting for them to speak.

Hint: look at the Agent lifecycle hooks in the docs: [Pipeline nodes & hooks](https://docs.livekit.io/agents/logic/nodes/). You're looking for a method that runs when the agent first enters the session.
