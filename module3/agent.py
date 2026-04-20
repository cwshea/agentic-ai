"""
module3/agent.py
================
Core Terraform Infrastructure Generation Agent for Module 3.

This module implements the LangChain-based agent that generates GCP Terraform
infrastructure code from repository analysis (Module 2 output) or direct
infrastructure requirements.

FRAMEWORK: LangChain + LangGraph (consistent with Module 2)
MODEL: Gemini via Vertex AI
PATTERN: ReAct (Reasoning + Acting) with tool calling
"""

from __future__ import annotations

import os
from typing import Any

from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import Runnable

from module3.config.models import get_chat_vertex_model
from module3.prompts.system_prompts import SYSTEM_PROMPT
from module3.tools.terraform_tools import ALL_TOOLS


def create_agent(
    *,
    verbose: bool = True,
    max_iterations: int = 20,
    region: str | None = None,
    streaming: bool = False,
) -> Runnable:
    """
    Create a Module 3 Terraform Infrastructure Generation Agent using LangGraph.

    Parameters
    ----------
    verbose : bool
        Print agent steps and tool calls. Default True for demos.
    max_iterations : int
        Maximum number of agent loop iterations. Default 20.
    region : str, optional
        GCP region override. Falls back to GCP_REGION env var.
    streaming : bool
        Enable streaming responses from the model.

    Returns
    -------
    Runnable
        Configured LangGraph agent ready to generate Terraform infrastructure.
    """
    gcp_location = region or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GCP_REGION") or "us-central1"

    model = get_chat_vertex_model(
        region=gcp_location,
        streaming=streaming,
        temperature=0.1,
        max_output_tokens=4096,
    )

    if verbose:
        print(f"  [Module 3 Agent] Using LangGraph ReAct Agent")
        print(f"  [Model] Gemini via Vertex AI (LangChain ChatGoogleGenerativeAI)")
        print(f"  [Location] {gcp_location}")
        print(f"  [Tools] {len(ALL_TOOLS)} Terraform generation tools")
        print(f"  [Temperature] 0.1 (deterministic code generation)")
        print()

    agent = create_react_agent(
        model,
        ALL_TOOLS,
        state_modifier=SYSTEM_PROMPT,
    )

    return agent


def generate_infrastructure(
    requirements: str | dict[str, Any],
    region: str = "us-central1",
    environment: str = "dev",
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Generate Terraform infrastructure from requirements.

    Parameters
    ----------
    requirements : str or dict
        Infrastructure requirements (Module 2 output or plain text).
    region : str
        GCP region for deployment. Default "us-central1".
    environment : str
        Environment name (dev/staging/prod). Default "dev".
    verbose : bool
        Print agent steps during generation.

    Returns
    -------
    dict
        Generated Terraform code and metadata.
    """
    agent = create_agent(verbose=verbose, region=region)

    if isinstance(requirements, dict):
        req_str = f"Infrastructure requirements: {requirements}"
    else:
        req_str = requirements

    query = f"""Generate Terraform infrastructure code for the following requirements:

{req_str}

Deployment details:
- GCP Region: {region}
- Environment: {environment}

Please:
1. Analyze the infrastructure requirements
2. Generate production-ready Terraform module code
3. Validate the generated code
4. Provide deployment instructions

Generate individual Terraform modules for each service type (network, cloud_run, cloud_sql, etc.).
"""

    result = agent.invoke({"messages": [("user", query)]})

    messages = result.get("messages", [])
    final_output = messages[-1].content if messages else ""

    return {
        "requirements": requirements,
        "region": region,
        "environment": environment,
        "output": final_output,
        "messages": messages,
    }


def validate_terraform_code(terraform_code: str, verbose: bool = True) -> dict[str, Any]:
    """
    Validate Terraform code using the agent's validation tools.

    Parameters
    ----------
    terraform_code : str
        Terraform HCL code to validate.
    verbose : bool
        Print validation steps.

    Returns
    -------
    dict
        Validation results.
    """
    agent = create_agent(verbose=verbose)

    query = f"""Validate the following Terraform configuration:

```hcl
{terraform_code}
```

Check for:
1. Syntax errors
2. Missing required blocks
3. Best practices
4. Security configurations

Provide a detailed validation report.
"""

    result = agent.invoke({"messages": [("user", query)]})

    messages = result.get("messages", [])
    final_output = messages[-1].content if messages else ""

    return {
        "terraform_code": terraform_code,
        "validation_output": final_output,
        "messages": messages,
    }
