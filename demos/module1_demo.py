#!/usr/bin/env python3
"""
demos/module1_demo.py
=====================
Live workshop demonstration for Module 1: Introduction to AI Agents.

Walks through every major concept from the slides using the real agent
running against simulated (mock) GCP data so no credentials are needed.

USAGE
-----
  # Recommended: mock mode (no GCP account needed)
  AGENT_MOCK_GCP=true python demos/module1_demo.py

  # Live GCP mode
  python demos/module1_demo.py --live

  # Run just one section
  AGENT_MOCK_GCP=true python demos/module1_demo.py --section 3

SECTIONS
--------
  1  Architecture anatomy  — the three layers in code before running
  2  The loop              — Think -> Act -> Observe, single query
  3  Multi-step reasoning  — compound question, multiple tool calls
  4  Human-in-the-loop     — agent finds a problem, escalates properly
  5  Model-agnostic swap   — one-line model change (Google <-> Model Garden)
  6  Context window        — multi-turn memory demonstration
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Rich output helpers
# ---------------------------------------------------------------------------

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    _c = Console()

    def header(text: str, color: str = "cyan") -> None:
        _c.rule(f"[bold {color}]{text}[/bold {color}]", style=color)

    def concept(text: str) -> None:
        _c.print(f"\n[bold yellow]💡 Module 1 Concept:[/bold yellow] [yellow]{text}[/yellow]")

    def user_says(text: str) -> None:
        _c.print(f"\n[bold green]USER ›[/bold green] [italic]{text}[/italic]")

    def box(title: str, body: str) -> None:
        _c.print(Panel(f"[dim]{body}[/dim]", title=f"[bold]{title}[/bold]", border_style="cyan"))

except ImportError:
    def header(text: str, color: str = "cyan") -> None:  # type: ignore[misc]
        print(f"\n{'═' * 62}\n  {text}\n{'═' * 62}")

    def concept(text: str) -> None:  # type: ignore[misc]
        print(f"\n💡 Concept: {text}")

    def user_says(text: str) -> None:  # type: ignore[misc]
        print(f"\nUSER › {text}")

    def box(title: str, body: str) -> None:  # type: ignore[misc]
        print(f"\n[ {title} ]\n{body}")


def pause(msg: str = "  ↵  Press Enter to continue...") -> None:
    try:
        input(msg)
    except KeyboardInterrupt:
        sys.exit(0)


# ---------------------------------------------------------------------------
# Section 1 — Architecture anatomy (no agent call)
# ---------------------------------------------------------------------------

def section_1_three_layers() -> None:
    header("SECTION 1 — The Three Layers", "cyan")
    box(
        "Architecture: Module 1 Skeleton",
        "Before we run anything, let's look at how the three layers are assembled in code.",
    )

    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │  REASONING LAYER  (config/models.py)                           │
  │                                                                 │
  │    model_id = get_vertex_model()                               │
  │        # "gemini-2.0-flash-001"                                │
  │        # temperature=0.1  ← low = deterministic infra work     │
  │                                                                 │
  │    # One-line swap to Model Garden open model:                 │
  │    model_id = get_model_garden_model(endpoint_id=...)          │
  └─────────────────────────────────────────────────────────────────┘
              │
  ┌─────────────────────────────────────────────────────────────────┐
  │  ORCHESTRATION LAYER  (agent.py)                               │
  │                                                                 │
  │    agent = Agent(                                               │
  │        name="gcp-infra-agent",                                 │
  │        model=model_id,                                          │
  │        instruction=SYSTEM_PROMPT,                              │
  │        tools=ALL_TOOLS,                                         │
  │    )                                                            │
  │    session_service = InMemorySessionService()  ← memory        │
  │    runner = Runner(agent=agent, ...)           ← runs the loop │
  └─────────────────────────────────────────────────────────────────┘
              │
  ┌─────────────────────────────────────────────────────────────────┐
  │  TOOLS LAYER  (tools/gcp_tools.py)                             │
  │                                                                 │
  │    def list_gcp_resources(      ← ADK reads signature + docs   │
  │        service_type: str,       ← LLM generates these args     │
  │        region: str,             │
  │    ) -> str:                    │
  │        '''List running GCP      │
  │        resources ...'''         │
  │        return gcp_client...     ← Python executes this         │
  └─────────────────────────────────────────────────────────────────┘
              │
  ┌─────────────────────────────────────────────────────────────────┐
  │  DEPLOYMENT  (app.py / Cloud Run)                              │
  │                                                                 │
  │    gcloud run deploy \\                                          │
  │      --source . --region us-central1                           │
  │                                                                 │
  │    # Same agent, managed runtime ────────────────────────────  │
  └─────────────────────────────────────────────────────────────────┘
""")

    concept(
        "The model is interchangeable. Swap the model_id "
        "and NOTHING ELSE changes — tools, prompt, and deployment are identical."
    )
    pause()


# ---------------------------------------------------------------------------
# Section 2 — The loop (single query, watch it run)
# ---------------------------------------------------------------------------

def section_2_the_loop(agent) -> None:
    header("SECTION 2 — Think → Act → Observe", "green")
    box(
        "The agent loop running live",
        "Watch the callback handler print each step. "
        "Notice that the agent calls a tool rather than guessing the answer.",
    )

    concept(
        "This is the fundamental difference from request-response AI. "
        "The agent uses tools to get current data, then reasons over it. "
        "It cannot hallucinate what services are running — it must look."
    )

    q = "How many Cloud Run services are running in us-central1?"
    user_says(q)
    print()
    response = agent(q)
    print(f"\n  AGENT › {response}\n")
    pause()


# ---------------------------------------------------------------------------
# Section 3 — Multi-step reasoning
# ---------------------------------------------------------------------------

def section_3_multi_step(agent) -> None:
    header("SECTION 3 — Multi-Step Reasoning", "blue")
    box(
        "Compound query requiring a plan across multiple tools",
        "The agent must decompose the goal, choose tools in sequence, and synthesise findings.",
    )

    concept(
        "A single tool call can't answer this. The agent must plan: "
        "1) get overview, 2) identify problems, 3) drill in, 4) assess health. "
        "Watch how many ACT steps appear."
    )

    q = (
        "Give me a complete health check of our us-central1 environment. "
        "If you find anything wrong, tell me what it is and what you'd recommend."
    )
    user_says(q)
    print()
    response = agent(q)
    print(f"\n  AGENT › {response}\n")

    concept(
        "The agent decomposed a broad goal into a sequence of tool calls. "
        "This is the planning capability of modern LLMs — no explicit workflow was coded."
    )
    pause()


# ---------------------------------------------------------------------------
# Section 4 — Human-in-the-loop
# ---------------------------------------------------------------------------

def section_4_hitl(agent) -> None:
    header("SECTION 4 — Human-in-the-Loop Pattern", "yellow")
    box(
        "Agent finds a problem and escalates — it does NOT act unilaterally",
        "This is Phase 1 (Assist) behaviour: observe, analyse, recommend, hand off.",
    )

    concept(
        "In Module 1, every proposed write operation goes through request_human_review. "
        "The agent's boundary is the analysis and the escalation ticket — not the fix. "
        "Trust is built by demonstrating accuracy before expanding autonomy."
    )

    q = (
        "The notification-svc Cloud Run service seems to have an issue. "
        "Investigate it and, if it needs attention, raise a review request for the team."
    )
    user_says(q)
    print()
    response = agent(q)
    print(f"\n  AGENT › {response}\n")

    concept(
        "Note the 🔔 HUMAN REVIEW REQUIRED block above. "
        "The agent investigated (multiple tool calls), identified the root cause, "
        "formed a recommendation, and raised a structured escalation — "
        "but did NOT restart the service. Explicit escalation, not silent action."
    )
    pause()


# ---------------------------------------------------------------------------
# Section 5 — Model-agnostic swap
# ---------------------------------------------------------------------------

def section_5_models() -> None:
    header("SECTION 5 — Model-Agnostic Architecture", "magenta")
    box(
        "One-line model swap — everything else unchanged",
        "The Google ADK framework decouples the reasoning engine from the agent logic.",
    )

    from module1.config.models import PROVIDER_INFO, print_provider_info

    print("\n  PROVIDER A — Google Gemini 2.0 Flash")
    print_provider_info("google")

    print("\n  PROVIDER B — Open model (via Vertex AI Model Garden)")
    print_provider_info("model_garden")

    print("""
  ┌─────────────────────────────────────────────────────────┐
  │  # Default: Gemini 2.0 Flash (Google on Vertex AI)      │
  │  agent = create_agent()                                  │
  │                                                          │
  │  # Switch to Model Garden — ONE LINE change:            │
  │  agent = create_agent(                                   │
  │      model_garden_endpoint=os.environ["MODEL_GARDEN_.."]│
  │  )                                                       │
  │                                                          │
  │  # Tools, system prompt, deployment:                    │
  │  # ← all unchanged ─────────────────────────────────── │
  └─────────────────────────────────────────────────────────┘

  How to set up a Vertex AI Model Garden endpoint:
    1. Google Cloud Console -> Vertex AI -> Model Garden
    2. Browse available models
    3. Choose model (e.g. Llama 3.1 8B — no subscription fee)
    4. Click Deploy -> select machine type -> wait for "Deployed"
    5. Copy the endpoint ID
    6. export MODEL_GARDEN_ENDPOINT="projects/.../endpoints/..."
    7. Run: python demos/module1_demo.py --model-garden

  Guide: https://cloud.google.com/vertex-ai/docs/model-garden/overview
""")

    mg_endpoint = os.getenv("MODEL_GARDEN_ENDPOINT")
    if mg_endpoint:
        from module1.agent import create_agent
        q = "How many Cloud Run services are running in us-central1?"
        print("  Running side-by-side comparison...\n")

        print("  [Gemini 2.0 Flash]")
        a_gemini = create_agent(verbose=False)
        t0 = time.time()
        r_gemini = a_gemini(q)
        print(f"  Response: {str(r_gemini)[:200]}")
        print(f"  Latency : {time.time()-t0:.2f}s\n")

        print("  [Model Garden]")
        a_mg = create_agent(model_garden_endpoint=mg_endpoint, verbose=False)
        t0 = time.time()
        r_mg = a_mg(q)
        print(f"  Response: {str(r_mg)[:200]}")
        print(f"  Latency : {time.time()-t0:.2f}s")
    else:
        print("  (Set MODEL_GARDEN_ENDPOINT to run a live side-by-side comparison)")

    pause()


# ---------------------------------------------------------------------------
# Section 6 — Context window / short-term memory
# ---------------------------------------------------------------------------

def section_6_context(agent) -> None:
    header("SECTION 6 — Context Window & Short-Term Memory", "red")
    box(
        "Multi-turn conversation — the agent remembers earlier turns",
        "InMemorySessionService keeps the full session history in context.",
    )

    concept(
        "Short-term memory lives INSIDE the session. "
        "The agent can refer back to what it said in the same session using "
        "vague references like 'that service' or 'the issue you found'. "
        "Long-term memory across sessions (Firestore / vector store) comes in Module 7."
    )

    turns = [
        "List all Cloud Run services in us-central1.",
        "Which of those has an issue?",
        "What would you recommend we investigate first?",
        "What was the ticket ID in the review request you raised?",
    ]

    print()
    for i, q in enumerate(turns, 1):
        user_says(f"[Turn {i}] {q}")
        print()
        response = agent(q)
        print(f"\n  AGENT › {response}\n")
        if i < len(turns):
            time.sleep(0.3)

    concept(
        "The agent resolved 'those', 'that', and 'you raised' correctly "
        "because the earlier turns are still in the session history. "
        "The session persists for the lifetime of the agent instance."
    )
    pause()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Module 1 Workshop Demo")
    parser.add_argument("--section", "-s", type=int, choices=range(1, 7), metavar="1-6")
    parser.add_argument("--live", action="store_true", help="Use real GCP credentials")
    parser.add_argument("--model-garden", action="store_true", help="Use Model Garden (needs MODEL_GARDEN_ENDPOINT)")
    args = parser.parse_args()

    if not args.live:
        os.environ["AGENT_MOCK_GCP"] = "true"
        print("  Mock mode ON  (pass --live to use real GCP credentials)\n")

    from module1.agent import create_agent

    mg_endpoint = os.getenv("MODEL_GARDEN_ENDPOINT") if args.model_garden else None
    agent = create_agent(model_garden_endpoint=mg_endpoint, verbose=True)

    header("GCP INFRASTRUCTURE AGENT — MODULE 1 DEMO", "bold cyan")
    print("""
  Use case: GCP Infrastructure Engineer building an agentic system
  to provision infrastructure, deploy microservices, and observe
  services running in Google Cloud.

  Module 1 scope: OBSERVE AND ANALYSE only.
  No infrastructure is created or modified.
  All proposed actions go through request_human_review.
""")
    pause("  ↵  Press Enter to begin...")

    sections = {
        1: section_1_three_layers,
        2: lambda: section_2_the_loop(agent),
        3: lambda: section_3_multi_step(agent),
        4: lambda: section_4_hitl(agent),
        5: section_5_models,
        6: lambda: section_6_context(agent),
    }

    if args.section:
        sections[args.section]()
    else:
        for fn in sections.values():
            fn()

    header("DEMO COMPLETE", "bold green")
    print("""
  ✅ You've seen:
     • Three layers assembled in code
     • Think → Act → Observe loop running live
     • Multi-step reasoning across multiple tool calls
     • Human-in-the-loop escalation pattern
     • Model-agnostic architecture (Gemini ↔ Model Garden in one line)
     • Short-term memory via session history

  🔜 Next: Module 2 — Agent Frameworks & Building Blocks
""")


if __name__ == "__main__":
    main()
