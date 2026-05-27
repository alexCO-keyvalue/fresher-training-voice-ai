# LiveKit Voice Agent Tutorial

A progressive tutorial for building voice AI agents with LiveKit Agents (Python).

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager).

2. Clone this repo and install dependencies:

```bash
git clone <repo-url>
cd fresher-training-voice-ai
uv sync
```

3. Copy `.env.example` to `.env.local` and fill in your LiveKit Cloud credentials:

```bash
cp .env.example .env.local
```

4. Download required model files (Silero VAD, turn detector):

```bash
uv run src/agent.py download-files
```

## Running

For use with a web frontend:

```bash
uv run src/agent.py dev
```

## Following Along

Each commit introduces one new concept. Use `git log --oneline` to see the progression and `git diff HEAD~1` to see what changed at each step.
