"""
module1
=======
Module 1: GCP Infrastructure Agent using Google ADK framework.

This module demonstrates the Module 1 framework approach with:
- Google ADK for agent orchestration
- Gemini via Vertex AI for reasoning
- Read-only GCP tools (Cloud Run, Compute Engine, Cloud SQL, Cloud Functions)
- Human-in-the-loop pattern
"""


def create_agent(**kwargs):
    """Lazy import to avoid requiring google-adk at module load time."""
    from module1.agent import create_agent as _create_agent
    return _create_agent(**kwargs)


__all__ = ["create_agent"]
