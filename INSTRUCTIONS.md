# Stage 4: Pipeline Nodes

## Goal

Understand how data flows through the STT -> LLM -> TTS pipeline and learn to intercept and modify it at each stage by overriding node methods.

## Background

The voice pipeline processes data in three stages:

```
Microphone audio
      |
  [stt_node]  -- converts audio to text (yields SpeechEvent objects)
      |
  [llm_node]  -- sends text to the LLM, gets response stream (yields ChatChunk objects)
      |
      +---------------------------+
      |                           |
  [tts_node]              [transcription_node]
  converts response        post-processes the LLM
  text to audio            output for display
      |
Speaker audio
```

Each of these nodes is a method on the `Agent` class. By default, they use `Agent.default.*_node()` which calls the STT/LLM/TTS you configured in `AgentSession`. You can override any of them to add custom logic -- filtering, transformation, logging, etc.

**Important distinction**: `stt_node` processes the *user's speech* (audio -> SpeechEvent), while `transcription_node` post-processes the *agent's LLM output* for display. If you want to clean up what the user said before it reaches the LLM, override `stt_node`, not `transcription_node`.

The key pattern is **async generators**: each node receives an async iterable and must return/yield the processed stream.

## Your Tasks

Open `src/agent.py` and implement the three TODO methods inside `TechSupportAgent`:

1. **TODO 1: `stt_node`** -- Strip filler words ("um", "uh", "like") from the user's speech before it reaches the LLM. Override `stt_node`, call `Agent.default.stt_node()`, and modify the `text` field on `SpeechEvent.alternatives` using `FILLER_PATTERN`.
2. **TODO 2: `tts_node`** -- Expand abbreviations ("API" -> "A P I") before TTS speaks them.
3. **TODO 3: `llm_node`** -- Enforce a hard character limit on LLM responses. Stream `ChatChunk` objects from `Agent.default.llm_node()`, track character count via `chunk.delta.content`, and stop the stream when `MAX_RESPONSE_CHARS` is reached.

Refer to the docs linked in each TODO comment for implementation guidance.

## Docs

- [Pipeline nodes & hooks](https://docs.livekit.io/agents/build/nodes/)

## Break It

- Remove the `tts_node` override and ask the agent "What is an API?" -- listen to how the TTS pronounces "API" without expansion.
- Add a mapping in `TTS_EXPANSIONS` that maps "Acme" to "ACME CORPORATION" and notice the difference.
- Set `MAX_RESPONSE_CHARS = 20` and watch the agent get cut off mid-sentence.

## Extend It

- Add a word count limit to `llm_node` instead of a character limit -- break on word boundaries so the response doesn't cut off mid-word.
