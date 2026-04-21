"""
config/models.py
================
Model provider configuration for the GCP Infrastructure Agent.

Configuration is loaded from gemini.yaml at the project root:

    llm:
        provider: gemini
        model: gemini-2.5-flash
        temperature: 1
        timeout: 600.0
    secrets:
        use_adc: true       # Application Default Credentials — no API key needed

PROVIDERS USED IN THIS PROJECT
--------------------------------
Both are available through Google Cloud:

  1. GOOGLE — Gemini via Vertex AI (configured in gemini.yaml)
     Access : gcloud auth application-default login
     Model  : gemini-2.5-flash (or any Gemini model)
     Why    : Primary reasoning engine — strong tool use and multi-step reasoning.

  2. MODEL GARDEN — Open models via Vertex AI Model Garden
     Access : Google Cloud Console -> Vertex AI -> Model Garden
              Deploy a model, then use the endpoint ID.
     Why    : Demonstrates model-agnostic architecture — the same
              ADK agent and tools work unchanged with a different engine.

SWITCHING MODELS (what to highlight in the workshop)
------------------------------------------------------
The model is the ONLY thing that changes. Tools, system prompt, orchestration
layer, and Cloud Run wrapper are all identical regardless of which model runs.

    # Gemini (default — configured in gemini.yaml)
    model_id = get_vertex_model()

    # Model Garden (open-source alternative)
    model_id = get_model_garden_model(endpoint_id="projects/.../endpoints/...")
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml


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
_SECRETS = _CONFIG.get("secrets", {})

DEFAULT_MODEL = _LLM.get("model", "gemini-2.5-flash")
DEFAULT_TEMPERATURE = _LLM.get("temperature", 0.1)
DEFAULT_TIMEOUT = _LLM.get("timeout", 600.0)
USE_ADC = _SECRETS.get("use_adc", True)


# ---------------------------------------------------------------------------
# Vertex AI setup (Application Default Credentials)
# ---------------------------------------------------------------------------

def configure_vertex_ai() -> None:
    """
    Configure google-genai to use Vertex AI with ADC.

    Call this before creating the ADK Agent. Requires:
      gcloud auth application-default login
    """
    if USE_ADC:
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        if project:
            os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project)
        location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)


# ---------------------------------------------------------------------------
# Model factory functions
# ---------------------------------------------------------------------------

def get_vertex_model(model_id: str | None = None) -> str:
    """
    Return the model ID string for use with Google ADK Agent.

    Reads the default from gemini.yaml. Falls back to gemini-2.5-flash.

    Prerequisites
    -------------
    1. GCP credentials configured (gcloud auth application-default login)
    2. Vertex AI API enabled in your project

    Parameters
    ----------
    model_id : str, optional
        Override the model from gemini.yaml.
    """
    return model_id or DEFAULT_MODEL


def get_model_garden_model(endpoint_id: str) -> str:
    """
    Return an endpoint ID for a Model Garden deployment for use with Google ADK.

    This demonstrates that the ADK agent is fully model-agnostic.
    The same tools, system prompt, and deployment wrapper work unchanged.

    HOW TO SET UP A MODEL GARDEN ENDPOINT
    ---------------------------------------
    1. Open Google Cloud Console -> Vertex AI -> Model Garden
    2. Browse available models
    3. Choose a model - recommended for this workshop:
         - Llama 3.1 8B Instruct (strong instruction following)
         - Mistral 7B Instruct   (capable, fast)
    4. Click "Deploy" -> select machine type (e.g. g2-standard-8)
    5. Wait for status "Deployed" in Vertex AI -> Online prediction -> Endpoints
    6. Copy the endpoint ID from the deployment details page
    7. Set env var:  export MODEL_GARDEN_ENDPOINT="projects/.../endpoints/..."
    8. Call this function or use: agent = create_agent(model_garden_endpoint=endpoint)

    Parameters
    ----------
    endpoint_id : str
        Vertex AI endpoint ID for the deployed model.
        Format: projects/<project>/locations/<region>/endpoints/<id>
    """
    return endpoint_id


# ---------------------------------------------------------------------------
# Convenience: model info for demo output
# ---------------------------------------------------------------------------

PROVIDER_INFO = {
    "google": {
        "name": f"Gemini ({DEFAULT_MODEL})",
        "vendor": "Google",
        "access": "Vertex AI with ADC (gcloud auth application-default login)",
        "model_id": DEFAULT_MODEL,
        "free_trial": "Free tier available — pay per token after",
        "context_window": "1,000,000 tokens",
        "strengths": "Strong tool use, multi-step reasoning, large context",
    },
    "model_garden": {
        "name": "Open model (e.g. Llama 3.1 8B Instruct)",
        "vendor": "Open source via Vertex AI Model Garden",
        "access": "Vertex AI -> Model Garden -> Deploy",
        "model_id": "Vertex AI endpoint ID (from deployment)",
        "free_trial": "Open models: no subscription fee — pay only for compute",
        "context_window": "Varies by model (4K-128K typically)",
        "strengths": "Open source, data stays in your VPC, no vendor lock-in",
        "setup_url": "https://cloud.google.com/vertex-ai/docs/model-garden/overview",
    },
}


def print_provider_info(provider: str = "google") -> None:
    """Print provider information for workshop demonstrations."""
    info = PROVIDER_INFO.get(provider, {})
    if not info:
        print(f"Unknown provider: {provider}")
        return
    print(f"\n  Model Provider: {info['vendor']}")
    print(f"  Model         : {info['name']}")
    print(f"  Access        : {info['access']}")
    print(f"  Model ID      : {info['model_id']}")
    print(f"  Free trial    : {info['free_trial']}")
    print(f"  Context window: {info['context_window']}")
    print(f"  Strengths     : {info['strengths']}")
    if "setup_url" in info:
        print(f"  Setup guide   : {info['setup_url']}")
    print()


class ModelConfig:
    """Simple namespace for model configuration constants."""
    DEFAULT_MODEL = DEFAULT_MODEL
    DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE
    DEFAULT_TIMEOUT = DEFAULT_TIMEOUT
