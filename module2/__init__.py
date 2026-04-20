"""
module2
=======
Module 2: Repository Analysis Agent using LangChain and LangGraph.

This module demonstrates the Module 2 framework approach with:
- LangChain for model interface and tool integration
- LangGraph for state machine workflow
- ChatGoogleGenerativeAI for Gemini via Vertex AI
- LangSmith for tracing and observability
"""

from module2.agent import create_agent

__all__ = ["create_agent"]
