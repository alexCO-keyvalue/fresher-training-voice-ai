# Stage 1: Setup and First Run

## Goal

Get your development environment running and have your first voice conversation with an AI agent. No code changes needed -- just configuration.

## The Voice Pipeline

When you talk to the agent, your voice flows through three AI models in sequence:

```
You speak
   |
   v
[STT] Speech-to-Text (Deepgram Nova-3)
   |  Converts your audio into text
   v
[LLM] Large Language Model (OpenAI GPT-4.1-mini)
   |  Reads the text and generates a response
   v
[TTS] Text-to-Speech (Cartesia Sonic-3)
   |  Converts the response text back into audio
   v
You hear the agent respond
```

The `AgentSession` in `src/agent.py` wires these three together. Silero VAD (Voice Activity Detection) listens for when you start and stop speaking.

## Steps

1. **Get LiveKit Cloud credentials**
   - Go to https://cloud.livekit.io and create a free account
   - Create a new project
   - Go to Settings > Keys and create an API key pair
   - You need three values: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

2. **Configure your environment**
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` and fill in your credentials.

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Download model files** (Silero VAD)
   ```bash
   uv run src/agent.py download-files
   ```

5. **Run the agent**
   ```bash
   uv run src/agent.py dev
   ```

6. **Connect to the Agent Playground**
   - Go to your LiveKit Cloud dashboard
   - Click "Agent Playground" (or go to https://cloud.livekit.io/projects/YOUR_PROJECT/playground)
   - You should see your agent connect
   - Start talking!

## Break It

- Change the LLM model to `openai/fake-model` in `src/agent.py`. What error do you get?
- Now change the STT model to something invalid. What's different about the error?
- What happens if you remove the `vad=` line entirely?

## Extend It

- Try changing the TTS voice UUID in `src/agent.py`. Where can you find other Cartesia voice IDs? (Hint: https://play.cartesia.ai)
- Change the LLM model to `openai/gpt-4.1` (the full model, not mini). Do you notice any difference in response quality or latency?
