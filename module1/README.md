# Module 1: GCP Infrastructure Agent

Google ADK-based agent for observing and analyzing GCP infrastructure resources.

## Overview

This module demonstrates the **Google ADK framework approach**, complementing Module 2's LangChain-based Repository Analysis Agent. Together, they form the foundation for multi-agent DevOps automation.

## What This Agent Does

1. **Observes** GCP infrastructure (Cloud Run, Compute Engine, Cloud SQL, Cloud Functions)
2. **Analyzes** resource health and identifies issues
3. **Recommends** specific remediation actions
4. **Escalates** via `request_human_review` — never modifies infrastructure directly

This is the **Phase 1 (Assist)** adoption pattern: the agent observes and recommends, humans act.

## Quick Start

```bash
# Authenticate with GCP (required for Gemini model)
gcloud auth application-default login

# Run demo in mock mode (no GCP resources needed)
AGENT_MOCK_GCP=true python demos/module1_demo.py

# Run specific demo section (1-6)
AGENT_MOCK_GCP=true python demos/module1_demo.py --section 4

# Run tests
AGENT_MOCK_GCP=true pytest tests/test_tools.py -v
```

## Architecture

### Framework: Google ADK

**Model**: Gemini via Vertex AI (configured in `gemini.yaml`)
**Orchestration**: ADK `Agent` + `Runner` + `InMemorySessionService`
**Tools**: 5 read-only GCP infrastructure tools
**Observability**: Event callbacks for Think → Act → Observe loop

### Three-Layer Architecture

| Layer | Component | File |
|-------|-----------|------|
| **Reasoning** | Gemini via Vertex AI | `config/models.py` |
| **Orchestration** | ADK Agent + Runner + Session | `agent.py` |
| **Tools** | 5 read-only GCP tools | `tools/gcp_tools.py` |

### Five Infrastructure Tools

| Tool | Purpose |
|------|---------|
| `list_gcp_resources(service_type, region)` | Cloud Run / Compute / Cloud SQL / Functions listings |
| `describe_resource(service_type, name, region)` | Detailed drill-down on a specific resource |
| `check_resource_health(service_type, name, region)` | Structured health verdict (healthy/degraded/critical) |
| `get_environment_summary(region)` | Cross-service overview with action items |
| `request_human_review(...)` | Human-in-the-loop escalation ticket |

## Framework Comparison: Module 1 vs Module 2

| Aspect | Module 1 (Google ADK) | Module 2 (LangChain) |
|--------|----------------------|---------------------|
| **Framework** | Google ADK | LangChain + LangGraph |
| **Model Interface** | Gemini via Vertex AI | `ChatGoogleGenerativeAI` |
| **Agent Pattern** | ADK `Agent` + `Runner` | `create_react_agent` |
| **Memory** | `InMemorySessionService` | LangGraph message state |
| **Observability** | Event callbacks | LangSmith tracing |
| **Tool Definition** | Plain functions (type hints + docstrings) | `@tool` decorator |
| **Use Case** | GCP infrastructure management | Repository analysis |

## Mock Data

With `AGENT_MOCK_GCP=true` the tools return realistic simulated data:

| Resource | Status | Notes |
|----------|--------|-------|
| `api-gateway-svc` (Cloud Run) | Healthy | 3/3 instances |
| `notification-svc` (Cloud Run) | Degraded | 1/2 instances, container crash |
| `prod-postgres-01` (Cloud SQL) | Healthy | HA enabled |
| `reporting-mysql` (Cloud SQL) | Degraded | No HA, no failover |
| `gke-node-01/02` (Compute) | Running | e2-standard-4 |
| `dev-sandbox` (Compute) | Terminated | Confirm intentional |

## Model-Agnostic Architecture

The agent supports swapping the model with one line:

```python
# Default: Gemini via Vertex AI (from gemini.yaml)
agent = create_agent()

# Alternative: Model Garden open model
agent = create_agent(model_garden_endpoint="projects/.../endpoints/...")
```

Tools, system prompt, session service, and HTTP server are completely unchanged.

## Usage

### Python API

```python
from module1.agent import create_agent

agent = create_agent(verbose=True)
response = agent("Give me a health summary of us-central1")
print(response)
```

### HTTP Server

```bash
# Start server
AGENT_MOCK_GCP=true python module1/app.py

# Invoke
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "List Cloud Run services in us-central1"}'
```

## Project Structure

```
module1/
├── agent.py              # ADK Agent + Runner + InfraAgent wrapper
├── app.py                # HTTP server / Cloud Run entrypoint
├── config/
│   └── models.py         # Gemini model config (from gemini.yaml)
└── tools/
    └── gcp_tools.py      # 5 read-only GCP tools
```

## Testing

```bash
# Run all Module 1 tests
AGENT_MOCK_GCP=true pytest tests/test_tools.py -v

# Run specific test class
AGENT_MOCK_GCP=true pytest tests/test_tools.py::TestCheckResourceHealth -v
```

## Demo Sections

Run `AGENT_MOCK_GCP=true python demos/module1_demo.py --section N`:

| # | Title | Key Concept |
|---|-------|-------------|
| 1 | Architecture anatomy | Three layers in code |
| 2 | The loop | Think → Act → Observe, live |
| 3 | Multi-step reasoning | Compound query, multiple tool calls |
| 4 | Human-in-the-loop | Agent escalates, doesn't act |
| 5 | Model swap | Gemini ↔ Model Garden |
| 6 | Context window | Multi-turn short-term memory |
