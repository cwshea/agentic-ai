"""
module2/agent.py
================
Core Repository Analysis Agent for Module 2.

This module implements the LangChain-based agent that analyzes git repositories
to identify applications, technology stacks, and GCP infrastructure requirements.

FRAMEWORK COMPARISON
--------------------
Module 1 uses Google ADK:
    from google.adk.agents import Agent
    agent = Agent(name="agent", model=model_id, instruction=prompt, tools=tools)

Module 2 uses LangChain + LangGraph:
    from langchain.agents import create_tool_calling_agent
    from langgraph.prebuilt import create_react_agent
    agent = create_react_agent(model, tools)

Both implement the same think-act-observe loop, but LangGraph provides
explicit state management and better observability through its graph structure.
"""

from __future__ import annotations

import os
from typing import Any

from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import Runnable

from module2.config.models import get_chat_vertex_model
from module2.prompts.system_prompts import SYSTEM_PROMPT
from module2.tools.repo_tools import ALL_TOOLS


# ---------------------------------------------------------------------------
# Agent Factory (LangGraph ReAct Agent)
# ---------------------------------------------------------------------------

def create_agent(
    *,
    verbose: bool = True,
    max_iterations: int = 15,
    region: str | None = None,
    streaming: bool = False,
) -> Runnable:
    """
    Create a Module 2 Repository Analysis Agent using LangGraph.

    This uses LangGraph's create_react_agent which provides a ReAct
    (Reasoning + Acting) loop with automatic tool calling.

    The agent uses:
    - ChatGoogleGenerativeAI (LangChain) for Gemini model access
    - LangGraph ReAct agent pattern
    - Automatic think-act-observe loop
    - Five repository analysis tools

    Parameters
    ----------
    verbose : bool
        Print agent steps and tool calls. Default True for demos.
    max_iterations : int
        Maximum number of agent loop iterations. Default 15.
    region : str, optional
        GCP region override. Falls back to GCP_REGION env var.
    streaming : bool
        Enable streaming responses from the model.

    Returns
    -------
    Runnable
        Configured LangGraph agent ready to analyze repositories.
    """
    gcp_location = region or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"

    model = get_chat_vertex_model(location=gcp_location, streaming=streaming)

    if verbose:
        print(f"  [Module 2 Agent] Using LangGraph ReAct Agent")
        print(f"  [Model] Gemini via Vertex AI (LangChain ChatGoogleGenerativeAI)")
        print(f"  [Location] {gcp_location}")
        print(f"  [Tools] {len(ALL_TOOLS)} repository analysis tools")
        print()

    agent = create_react_agent(
        model,
        ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
    )

    return agent


# ---------------------------------------------------------------------------
# Graph-Based Agent Factory (LangGraph approach)
# ---------------------------------------------------------------------------

def create_graph_agent(
    *,
    verbose: bool = True,
    region: str | None = None,
) -> Runnable:
    """
    Create a Module 2 Repository Analysis Agent using LangGraph state machine.

    This approach uses the explicit workflow defined in analysis_graph.py
    with five stages: scan -> detect -> analyze -> map -> synthesize.

    Parameters
    ----------
    verbose : bool
        Print workflow stage transitions. Default True.
    region : str, optional
        GCP region override.

    Returns
    -------
    Runnable
        Compiled LangGraph workflow ready to invoke.
    """
    from langgraph.prebuilt import create_react_agent

    from module2.config.models import get_chat_vertex_model
    from module2.tools.repo_tools import ALL_TOOLS

    gcp_location = region or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"

    model = get_chat_vertex_model(location=gcp_location)

    if verbose:
        print(f"  [Module 2 Graph Agent] Using LangGraph state machine")
        print(f"  [Model] Gemini via Vertex AI (ChatGoogleGenerativeAI)")
        print(f"  [Workflow] scan -> detect -> analyze -> map -> synthesize")
        print()

    agent = create_react_agent(
        model,
        ALL_TOOLS,
        state_modifier=SYSTEM_PROMPT,
    )

    return agent


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def analyze_repository(repo_path: str, verbose: bool = True) -> dict[str, Any]:
    """
    Analyze a repository and return structured results.

    Parameters
    ----------
    repo_path : str
        Absolute path to the git repository to analyze.
    verbose : bool
        Print agent steps during analysis.

    Returns
    -------
    dict
        Analysis results with applications, stacks, and GCP requirements.
    """
    agent = create_agent(verbose=verbose)

    query = f"""Analyze the git repository at: {repo_path}

Please:
1. Scan the repository structure
2. Detect all applications/services
3. Analyze the technology stack for each application
4. Map dependencies to GCP infrastructure requirements
5. Provide a comprehensive analysis report

Return the results as structured JSON."""

    result = agent.invoke({"messages": [("user", query)]})

    messages = result.get("messages", [])
    final_output = messages[-1].content if messages else ""

    return {
        "repo_path": repo_path,
        "output": final_output,
        "messages": messages,
    }
