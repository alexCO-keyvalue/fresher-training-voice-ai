# Stage 7: Multi-Agent Handoffs

## Goal

Build a multi-agent system where specialist agents hand off to each other using `session.update_agent()`, passing context between them.

## Background

A single agent can't do everything well. In production, you split responsibilities across specialist agents:

```
User calls in
      |
  [TriageAgent]  -- "What do you need help with?"
      |
   /     \
  v       v
[TechnicalAgent]   [BillingAgent]
  |                   |
  v                   v
"Let me help with     "Let me look up
 that bug..."          your invoice..."
```

Each agent has its own instructions, tools, and personality. When the user's needs change, agents hand off using `session.update_agent()`. The key question is: **what happens to conversation history during a handoff?**

## What's Already Built

Open `src/agent.py` and study the code:

- **`TriageAgent`** -- fully implemented. Routes users to technical or billing support. Has `transfer_to_technical` and `transfer_to_billing` tools.
- **`TechnicalAgent`** -- fully implemented. Has `lookup_ticket`, `create_ticket`, and `transfer_to_triage` tools.
- **`BillingAgent`** -- just a stub (`pass`). This is what you need to build.

The entrypoint already starts with `TriageAgent`. When the user says they have a billing question, the triage agent will try to transfer to `BillingAgent` -- but it won't work until you implement it.

## Your Task

Build `BillingAgent` from scratch by studying `TriageAgent` and `TechnicalAgent` as examples:

1. Accept `user_context` in `__init__` and use it in the instructions
2. Implement `on_enter()` to greet the user as the billing specialist
3. Implement a `lookup_invoice` tool using `INVOICE_DATABASE`
4. Implement a `transfer_to_triage` tool to hand back without losing context

Pay attention to how context flows: `self.user_context` is passed between agents so each one can personalize its instructions.

## Docs

- [Agents & handoffs](https://docs.livekit.io/agents/logic/turns/agents-and-handoffs/)

## Break It

- Remove the `transfer_to_triage` tool from your `BillingAgent`. Ask the billing agent a technical question. What does it do?
- Remove the routing instructions from `TriageAgent` but keep the transfer tools. Does it still route correctly? (Tools have docstrings -- does the LLM figure it out?)

## Extend It

- After the billing issue is resolved, make `BillingAgent` transfer to `TechnicalAgent` directly (skipping triage) if the user mentions a technical problem. How do you preserve context across a three-agent chain?
