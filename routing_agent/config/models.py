"""
routing-agent/config/models.py
===============================
Model configuration for routing agent.

Uses ChatGoogleGenerativeAI (Gemini via Vertex AI) for intent classification.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from langchain_google_genai import ChatGoogleGenerativeAI


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "gemini.yaml"


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


_CONFIG = _load_config()
_LLM = _CONFIG.get("llm", {})
DEFAULT_MODEL = _LLM.get("model", "gemini-2.5-flash")


def get_chat_vertex_model(
    region: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_output_tokens: int = 1024,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI:
    """
    Get a configured ChatGoogleGenerativeAI model for intent classification.

    Uses temperature=0.0 for deterministic classification.
    """
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    gcp_location = region or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"

    return ChatGoogleGenerativeAI(
        model=model or DEFAULT_MODEL,
        vertexai=True,
        project=gcp_project,
        location=gcp_location,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        **kwargs,
    )
