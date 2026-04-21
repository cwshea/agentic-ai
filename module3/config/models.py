"""
module3/config/models.py
========================
Model configuration for Module 3 Terraform Generation Agent.

Uses Gemini via Vertex AI (from gemini.yaml) for both generation and
evaluation (LLM-as-judge). The judge uses temperature=0.0 for
deterministic scoring.
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
    model: str | None = None,
    region: str | None = None,
    temperature: float = 0.1,
    max_output_tokens: int = 4096,
    streaming: bool = False,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI:
    """Return a ChatGoogleGenerativeAI model for Terraform code generation."""
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    gcp_location = region or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"

    return ChatGoogleGenerativeAI(
        model=model or DEFAULT_MODEL,
        vertexai=True,
        project=gcp_project,
        location=gcp_location,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        streaming=streaming,
        **kwargs,
    )


def get_judge_model(
    model: str | None = None,
    region: str | None = None,
    temperature: float = 0.0,
    max_output_tokens: int = 4096,
    **kwargs: Any,
) -> ChatGoogleGenerativeAI:
    """Return a ChatGoogleGenerativeAI model for LLM-as-judge evaluation (temperature=0.0)."""
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
