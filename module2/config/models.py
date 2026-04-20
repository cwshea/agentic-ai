"""
module2/config/models.py
========================
Model provider configuration for Module 2 Repository Analysis Agent.

This module uses LangChain's ChatGoogleGenerativeAI for model access, demonstrating
the LangChain framework approach compared to Module 1's Google ADK.

FRAMEWORK COMPARISON
--------------------
Module 1 (Google ADK):
    from google.adk.agents import Agent
    agent = Agent(name="agent", model="gemini-2.5-pro", ...)

Module 2 (LangChain):
    from langchain_google_genai import ChatGoogleGenerativeAI
    model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", ...)

Both use Gemini via Vertex AI, but Module 1 uses Google ADK directly
while Module 2 uses LangChain's wrapper which integrates with LCEL,
LangGraph, and LangSmith.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from langchain_google_genai import ChatGoogleGenerativeAI


# ---------------------------------------------------------------------------
# Load configuration from gemini.yaml
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "gemini.yaml"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


_CONFIG = _load_config()
_LLM = _CONFIG.get("llm", {})

DEFAULT_MODEL = _LLM.get("model", "gemini-2.5-pro")
DEFAULT_TEMPERATURE = _LLM.get("temperature", 0.1)


def get_chat_vertex_model(
    model: str | None = None,
    project: str | None = None,
    location: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int = 4096,
    streaming: bool = False,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI:
    """
    Return a LangChain ChatGoogleGenerativeAI model configured for Gemini.

    Reads defaults from gemini.yaml. Uses Application Default Credentials.

    Prerequisites
    -------------
    1. GCP credentials configured (gcloud auth application-default login)
    2. Vertex AI API enabled in your project

    Parameters
    ----------
    model : str, optional
        Vertex AI model name. Defaults to gemini.yaml config.
    project : str, optional
        GCP project ID. Falls back to GOOGLE_CLOUD_PROJECT env var.
    location : str, optional
        GCP region. Falls back to GOOGLE_CLOUD_LOCATION / GCP_REGION env vars.
    temperature : float, optional
        Defaults to gemini.yaml config or 0.1.
    max_output_tokens : int
        Max response tokens. 4096 is sufficient for structured analysis.
    streaming : bool
        Enable streaming responses.
    **kwargs : Any
        Additional ChatGoogleGenerativeAI parameters.

    Returns
    -------
    ChatGoogleGenerativeAI
        Configured LangChain ChatGoogleGenerativeAI model instance.
    """
    gcp_project = project or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    gcp_location = location or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"
    temp = temperature if temperature is not None else DEFAULT_TEMPERATURE

    return ChatGoogleGenerativeAI(
        model=model or DEFAULT_MODEL,
        vertexai=True,
        project=gcp_project,
        location=gcp_location,
        temperature=temp,
        max_output_tokens=max_output_tokens,
        streaming=streaming,
        **kwargs,
    )


class ModelConfig:
    """Configuration constants for Module 2 models."""

    DEFAULT_MODEL = DEFAULT_MODEL
    DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_STREAMING = False
