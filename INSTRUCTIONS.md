# Stage 3: Turn Detection and Interruptions

## Goal

Understand how VAD (Voice Activity Detection), turn detection, and interruption handling affect the flow of a voice conversation using the unified `TurnHandlingOptions` API.

## Background

By default, the agent uses VAD to detect when you start and stop speaking. VAD works by detecting **silence** -- when you stop making sound for long enough, it assumes you're done.

But humans pause mid-sentence all the time ("I was trying to... you know... open the dashboard"). VAD alone would cut you off during those pauses.

A **turn detector** (`inference.TurnDetector()`) is a built-in audio-based model that analyzes what you've said and decides whether you've actually finished your thought. It's much smarter than silence detection alone.

**Preemptive generation** is a latency optimization: the LLM starts generating a response while the turn detector is still deciding. If you keep talking, the partial response is discarded. If you're done, the response is already partly generated. This is enabled by default in LiveKit Agents v1.5+.


## Your Tasks

Open `src/agent.py` and complete the three TODOs.

Run the agent after each change and notice the difference in conversation flow.

## Docs

- [Turn detection & interruptions overview](https://docs.livekit.io/agents/logic/turns/)
- [Turn detector](https://docs.livekit.io/agents/logic/turns/turn-detector/)
- [Turn-taking tuning (preemptive generation, endpointing)](https://docs.livekit.io/agents/logic/turns/tuning/)
- [Turn handling options reference](https://docs.livekit.io/reference/agents/turn-handling-options/)

## Break It

- Set `interruption={"enabled": True}` and try talking over the agent while it's speaking. What happens?
- Disable preemptive generation (`preemptive_generation={"enabled": False}`) and time how long it takes the agent to start responding after you finish speaking. Now enable it and compare.

## Extend It

- Look up `TurnHandlingOptions` in the LiveKit docs and try configuring `endpointing` with custom `min_delay` and `max_delay` values. What do these do?
- Try the `"mode": "adaptive"` interruption mode. How does it differ from simple enabled/disabled?
