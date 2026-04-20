# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Workshop code for the **AI Agent Learning Series** — three modules demonstrating agentic AI patterns for cloud infrastructure management. All modules target GCP. This is educational/demo code, not a production application.

## Build & Run

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Verify installation
python verify_installation.py
```

## Test Commands

```bash
# All tests (mock mode — no cloud credentials or repos needed)
AGENT_MOCK_GCP=true AGENT_MOCK_REPO=true pytest tests/ -v

# Individual module tests
AGENT_MOCK_GCP=true pytest tests/test_tools.py -v           # Module 1
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v     # Module 2
AGENT_MOCK_REPO=true pytest tests/test_module3_tools.py -v  # Module 3
AGENT_MOCK_REPO=true pytest tests/test_routing_agent.py -v  # Routing
AGENT_MOCK_REPO=true pytest tests/test_evaluation.py -v     # Evaluation
```

## Running Demos & Servers

```bash
# Demo scripts with numbered sections (--section N for specific section)
AGENT_MOCK_GCP=true python demos/module1_demo.py
AGENT_MOCK_REPO=true python demos/module2_demo.py
AGENT_MOCK_REPO=true python demos/module3_demo.py

# HTTP servers (each module runs independently)
AGENT_MOCK_GCP=true python module1/app.py   # port 8080, POST /invocations
AGENT_MOCK_REPO=true python module2/app.py  # port 8081, POST /analyze
AGENT_MOCK_REPO=true python module3/app.py  # port 8082, POST /generate
python routing_agent/app.py                  # port 8083, POST /route, /classify
# All servers expose GET /ping for health checks
```

## Architecture

**Two agent frameworks, same think-act-observe pattern:**

- **Module 1** uses **Google ADK** (`google-adk`): `Agent` → `Runner` + `InMemorySessionService` → tool functions (plain Python functions with type hints)
- **Module 2** uses **LangChain + LangGraph** (`langchain-google-genai`): `ChatGoogleGenerativeAI` → `create_react_agent` → tools decorated with `@tool` from `langchain_core.tools`
- **Module 3** uses **LangChain + LangGraph** (`langchain-google-genai`): `ChatGoogleGenerativeAI` → `create_react_agent` → tools decorated with `@tool` from `langchain_core.tools`
- **Routing Agent** uses LangChain but **no agent loop** — a single-shot `prompt | model | StrOutputParser()` chain with `temperature=0.0` for deterministic classification. Routes based on confidence: >=0.7 routes, 0.5-0.7 asks for clarification, <0.5 rejects.

Each module follows the same layout: `agent.py` (agent factory), `app.py` (HTTP server), `config/models.py` (model config), `tools/` (tool implementations), `prompts/` (system prompts).

**Cross-module flow:** Module 2 analyzes a repo → Module 3 generates Terraform from analysis → evaluation pipeline scores the output. The routing agent classifies intent and forwards to the right module's HTTP server.

### Tool Output Convention

All tools across all modules return JSON strings with a consistent envelope: `{tool, timestamp, region/mock_mode, data}`. This is done via a `_wrap()` helper in each tools file. New tools must follow this pattern — the agents parse this structured output.

### Module 2 Dual Approaches

Module 2 provides two orchestration styles in separate files:
- `agent.py` with `create_agent()` — standard ReAct loop via `create_react_agent`
- `workflows/analysis_graph.py` with `create_graph_agent()` — explicit LangGraph state machine with 5 stages: scan → detect → analyze → map → synthesize

### Module 1 Three-Layer Architecture

Module 1 explicitly separates: (1) Reasoning layer (Gemini via Vertex AI), (2) Orchestration layer (ADK `Agent` + `Runner` + `InMemorySessionService` + event callbacks), (3) Tool layer (5 read-only GCP tools). This structure is intentional for the workshop slides.

Module 1 is model-agnostic: same tools/prompts work with Gemini (Vertex AI) or open models (Model Garden) — swap one line in `config/models.py`. ADK tools are plain Python functions (no decorator needed) — ADK infers the schema from type hints and docstrings.

## Evaluation Pipeline

Module 3 uses an **LLM-as-judge** pattern with intentionally different models to avoid self-evaluation bias:
- **Generator**: Claude Sonnet 4 at `temperature=0.1` (deterministic code generation)
- **Judge**: Claude Opus 4 at `temperature=0.0` (deterministic evaluation)

Evaluation dimensions with weights: Syntax 40%, Completeness 20%, Best practices 20%, Security 20%.

**ISV integrations** (Patronus, Deepchecks, Comet ML) are optional — all gracefully fall back to mock implementations if their API keys are absent. Test datasets live in `evaluation/datasets/`.

## Key Environment Variables

- `AGENT_MOCK_GCP=true` — Module 1: simulated GCP resources instead of real API calls
- `AGENT_MOCK_REPO=true` — Modules 2-3: simulated repository instead of real git repo
- `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` — enables LangSmith tracing
- `GOOGLE_CLOUD_PROJECT` — GCP project ID (Module 1)
- `GCP_REGION` — GCP region override (Module 1, default: us-central1)

## Test Patterns

Tests use pytest fixtures to set/restore mock environment variables:
```python
@pytest.fixture
def enable_mock_mode():
    original = os.environ.get("AGENT_MOCK_REPO")
    os.environ["AGENT_MOCK_REPO"] = "true"
    yield
    # restore original value
```
All tests run in mock mode — no GCP credentials or real repos needed. Mock data includes realistic GCP resources (healthy/degraded states) and sample repos (Node.js, Python, monorepo) in `tests/fixtures/`.

## Model Configuration

All modules use Gemini via Vertex AI (configured in `gemini.yaml`, default `gemini-2.5-pro`). All model swaps are one line in the respective `config/models.py`.

## Development

`.vscode/launch.json` has 16 pre-configured debug configurations for all modules, demos, and tests.
