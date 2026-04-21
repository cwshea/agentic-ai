"""
agent.py
========
Core GCP Infrastructure Agent — Module 1.

This file is the heart of the skeleton. It assembles all three layers
(Reasoning, Orchestration, Tools) into a working Google ADK Agent.

MODULE 1 CONCEPTS IMPLEMENTED
-------------------------------

  REASONING LAYER
  ───────────────
  Gemini 2.0 Flash via Vertex AI (Google Cloud).
  Optionally replaceable with an open model from Vertex AI Model Garden
  — the rest of the file is unchanged. This is the model-agnostic property
  of the Google ADK framework that the module highlights.

  ORCHESTRATION LAYER
  ───────────────────
  • Google ADK Agent  : drives the Think → Act → Observe loop automatically
  • System prompt     : defines the agent persona, scope, and hard constraints
  • Session service   : context window management (in-memory session history)
  • Event callbacks   : lightweight observability — prints each loop step to
                        console so workshop attendees can watch the loop run

  TOOLS LAYER
  ──────────
  • list_gcp_resources     — Cloud Run / Compute Engine / Cloud SQL / Cloud Functions
  • describe_resource      — detailed drill-down on a specific resource
  • check_resource_health  — opinionated health assessment
  • get_environment_summary — cross-service overview
  • request_human_review   — human-in-the-loop escalation

  All Module 1 tools are READ-ONLY. The only action path is
  request_human_review, which creates a structured escalation record.

CONTEXT WINDOW MANAGEMENT
--------------------------
Google ADK's InMemorySessionService keeps the full conversation history
for each session. This implements the short-term memory concept from the
slides — the agent can refer back to earlier turns within the same session.

USAGE
-----
    # Default (Gemini 2.0 Flash via Vertex AI, verbose)
    from agent import create_agent
    agent = create_agent()
    response = agent("Give me a health summary of us-central1")
    print(response)

    # Model Garden alternative (same agent logic, different model)
    import os
    from agent import create_agent
    agent = create_agent(model_garden_endpoint=os.environ["MODEL_GARDEN_ENDPOINT"])
    response = agent("List Cloud Run services in us-central1")
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# The google-genai library logs a spurious warning when ADK's debug formatter
# accesses GenerateContentResponse.text on a response that contains
# function_call parts. This is an upstream issue in google-genai's
# google_llm.py debug logging — silence it here.
logging.getLogger("google.genai.types").setLevel(logging.ERROR)

from module1.config.models import configure_vertex_ai, get_vertex_model, get_model_garden_model
from module1.tools.gcp_tools import ALL_TOOLS


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a GCP Infrastructure Agent working with an engineering \
team that builds and operates microservices on Google Cloud.

## Your Role in Module 1

You are operating in OBSERVE AND ANALYSE mode. Your job is to:

1. **Observe** — use your tools to retrieve the current state of GCP infrastructure.
   Never guess or rely on prior knowledge about what is deployed. Always call a tool.

2. **Analyse** — identify issues, risks, and anomalies in what you observe.

3. **Reason** — explain your findings clearly, citing the data returned by tools.

4. **Recommend** — propose specific, concrete next steps.

5. **Escalate** — use the `request_human_review` tool for any action that would
   modify infrastructure. Do not describe what you "would" do — raise a formal
   review request with your full analysis so a human can act on it.

## Hard Constraints (Module 1)

- You have NO ability to create, modify, or delete any GCP resource directly.
- ALL proposed write operations MUST go through `request_human_review`.
- If you identify something that needs fixing, your job ends at raising the review
  request — not at actually fixing it.

## Tool Usage

- Start broad: use `get_environment_summary` for overview questions.
- Drill in: use `list_gcp_resources` then `describe_resource` for specifics.
- For health questions: use `check_resource_health` which returns a structured verdict.
- Escalate: use `request_human_review` with complete context when action is needed.
- Always pass `region` explicitly when the user mentions one.

## Response Format

Structure responses as:
  **Summary**: one-sentence answer
  **Findings**: bullet list of what you observed (cite tool output)
  **Recommendations**: concrete next steps (or "None — no action required")

Keep technical responses factual and concise. Use severity language:
  critical (immediate action) / degraded (investigate soon) / healthy (no action)
"""


# ---------------------------------------------------------------------------
# Callable agent wrapper
# ---------------------------------------------------------------------------

class InfraAgent:
    """
    Wraps a Google ADK Agent + Runner into a callable interface.

    This provides the same simple `agent("query")` API that the workshop
    demos expect, while using ADK's Runner and SessionService underneath.
    """

    def __init__(
        self,
        agent: Agent,
        runner: Runner,
        session_service: InMemorySessionService,
        *,
        app_name: str = "gcp_infra_agent",
        user_id: str = "workshop-user",
        verbose: bool = True,
    ) -> None:
        self._agent = agent
        self._runner = runner
        self._session_service = session_service
        self._app_name = app_name
        self._user_id = user_id
        self._verbose = verbose
        self._step = 0
        self._session_id: str | None = None
        self._loop = asyncio.new_event_loop()

    def __call__(self, prompt: str) -> str:
        return self._loop.run_until_complete(self._invoke(prompt))

    def close(self) -> None:
        """Shut down pending async tasks and close the event loop."""
        if self._loop.is_closed():
            return
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.run_until_complete(self._loop.shutdown_default_executor())
        self._loop.close()

    def __del__(self) -> None:
        self.close()

    async def _invoke(self, prompt: str) -> str:
        if self._session_id is None:
            session = await self._session_service.create_session(
                app_name=self._app_name, user_id=self._user_id
            )
            self._session_id = session.id

        content = types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        )

        response_text = ""
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=self._session_id,
            new_message=content,
        ):
            if self._verbose:
                self._print_event(event)
            if event.is_final_response() and event.content and event.content.parts:
                text_parts = [
                    p.text for p in event.content.parts
                    if p.text is not None
                ]
                if text_parts:
                    response_text = "\n".join(text_parts)

        return response_text

    def _print_event(self, event: Any) -> None:
        """Print Think → Act → Observe loop steps for workshop visibility."""
        function_calls = event.get_function_calls()
        function_responses = event.get_function_responses()

        if function_calls:
            for fc in function_calls:
                self._step += 1
                name = fc.name or "?"
                args = fc.args or {}
                parts = [f"{k}={repr(v)}" for k, v in args.items()]
                print(f"\n  🔧 [Step {self._step}] ACT → {name}({', '.join(parts)})")
        elif function_responses:
            for fr in function_responses:
                name = fr.name or "?"
                print(f"  ✓  OBSERVE ← {name} returned (added to context)")
        elif event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call or part.function_response:
                    continue
                if part.thought:
                    print(f"\n  🧠 THINK  (reasoning over context...)")


# ---------------------------------------------------------------------------
# Agent factory
# ---------------------------------------------------------------------------

def create_agent(
    *,
    model_garden_endpoint: str | None = None,
    verbose: bool = True,
    region: str | None = None,
) -> InfraAgent:
    """
    Assemble and return the Module 1 GCP Infrastructure Agent.

    This function is the integration point of all three layers:

      Reasoning    → Gemini 2.0 Flash (or Model Garden endpoint)
      Orchestration→ Google ADK Agent + InMemorySessionService
      Tools        → ALL_TOOLS (list / describe / health / summary / escalate)

    Parameters
    ----------
    model_garden_endpoint : str, optional
        Vertex AI endpoint ID for a Model Garden model. When provided,
        uses the open model instead of Gemini. All other agent configuration
        remains identical — demonstrating model-agnostic architecture.
    verbose : bool
        Print Think → Act → Observe loop steps. Default True for demos.
    region : str, optional
        GCP region override. Falls back to GCP_REGION env var.

    Returns
    -------
    InfraAgent
        Callable agent wrapper — use as `agent("your question")`.
    """
    gcp_region = region or os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"

    # ── CONFIGURE VERTEX AI (ADC from gemini.yaml) ───────────────────────────
    configure_vertex_ai()

    # ── REASONING LAYER ──────────────────────────────────────────────────────
    if model_garden_endpoint:
        model_id = get_model_garden_model(endpoint_id=model_garden_endpoint)
        print(f"  [Agent] Using open model via Vertex AI Model Garden")
        print(f"          Endpoint: {model_garden_endpoint[:60]}...")
    else:
        model_id = get_vertex_model()
        print(f"  [Agent] Using {model_id} via Vertex AI (ADC)")

    # ── ORCHESTRATION LAYER: assemble the agent ───────────────────────────────
    agent = Agent(
        name="gcp_infra_agent",
        model=model_id,
        description="GCP Infrastructure Agent for observing and analysing cloud resources.",
        instruction=SYSTEM_PROMPT,
        tools=ALL_TOOLS,
    )

    # ── SESSION SERVICE (short-term memory) ──────────────────────────────────
    session_service = InMemorySessionService()

    # ── RUNNER ───────────────────────────────────────────────────────────────
    runner = Runner(
        agent=agent,
        app_name="gcp_infra_agent",
        session_service=session_service,
    )

    return InfraAgent(
        agent=agent,
        runner=runner,
        session_service=session_service,
        verbose=verbose,
    )
