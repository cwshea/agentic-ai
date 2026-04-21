# AI Agent Learning Series

Hands-on demonstration code for the **AI Agent Learning**.

**Use case:** A Cloud Infrastructure Engineer is building an agentic system that can provision infrastructure, deploy and build microservices, and observe those services running in the cloud.

This repository contains multiple modules demonstrating different agent frameworks and patterns:
- **Module 1**: Google ADK-based Infrastructure Agent (observe and analyze GCP resources)
- **Module 2**: LangChain-based Repository Analysis Agent (analyze git repos for deployment planning)
- **Module 3**: Terraform Generation Agent with Evaluation & Routing (generate infrastructure code with quality assurance)

Future modules will add multi-agent orchestration, long-term memory, and full autonomy.

---

## Modules Overview

### Module 1: GCP Infrastructure Agent (Google ADK Framework)

Observes and analyzes GCP infrastructure using Google Agent Development Kit (ADK).

**Key Concepts:**
- Three Layers (Reasoning / Orchestration / Tools)
- Think → Act → Observe loop with event callbacks
- Context window / short-term memory
- Human-in-the-loop pattern
- Model-agnostic architecture

**Tools:** 5 read-only GCP tools (Cloud Run, Compute Engine, Cloud SQL, Cloud Functions)

[See module1/README.md for details](module1/)

### Module 2: Repository Analysis Agent (LangChain Framework)

Analyzes git repositories to identify applications and GCP infrastructure requirements using LangChain + LangGraph.

**Key Concepts:**
- LangChain `ChatGoogleGenerativeAI` model interface
- `AgentExecutor` and LangGraph state machines
- Repository scanning and dependency analysis
- GCP service mapping from dependencies
- LangSmith tracing for observability

**Tools:** 5 repository analysis tools (scan, detect, analyze, map)

[See module2/README.md for details](module2/)

### Module 3: Terraform Generation Agent with Evaluation (LangChain Framework)

Generates Terraform infrastructure code for GCP from requirements with comprehensive evaluation and quality assurance using LangChain + LangGraph.

**Key Concepts:**
- Terraform infrastructure code generation
- LLM-as-judge evaluation pattern
- Automated evaluation pipelines
- ISV integrations (Patronus AI, Deepchecks, Comet ML)
- Routing agent for intent classification
- Self-correction pattern

**Tools:** 5 Terraform generation tools (analyze, generate, validate, list, test)

**Additional Components:**
- **Routing Agent**: Intent classification and request routing
- **Evaluation System**: Automated quality assessment for Module 2 & 3
- **ISV Integrations**: Patronus AI, Deepchecks, Comet ML

[See module3/README.md for details](module3/)

---

## Project Structure

```
infra-agent/
├── module1/                    # GCP Infrastructure Agent (Google ADK)
│   ├── agent.py               # Core agent with three layers
│   ├── app.py                 # HTTP server / Cloud Run entrypoint
│   ├── config/models.py       # Gemini + Model Garden configs
│   └── tools/gcp_tools.py     # 5 read-only GCP tools
│
├── module2/                    # Repository Analysis Agent (LangChain)
│   ├── agent.py               # LangChain agent factory
│   ├── app.py                 # HTTP server entrypoint
│   ├── config/models.py       # ChatGoogleGenerativeAI configuration
│   ├── tools/repo_tools.py    # 5 repository analysis tools
│   ├── workflows/             # LangGraph state machine
│   └── prompts/               # System prompts
│
├── demos/
│   ├── module1_demo.py        # Module 1 workshop demo (6 sections)
│   └── module2_demo.py        # Module 2 workshop demo (6 sections)
│
├── tests/
│   ├── test_tools.py          # Module 1 tests
│   ├── test_repo_tools.py     # Module 2 tests
│   └── fixtures/              # Test repository fixtures
│
├── gemini.yaml                # Gemini model configuration (ADC)
└── requirements.txt           # Dependencies for all modules
```

---

## Quick Start

### Setup

```bash
# 1. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

### Module 1: GCP Infrastructure Agent

```bash
# Authenticate with GCP (required for Gemini via Vertex AI)
gcloud auth application-default login

# Run demo in mock mode (no GCP resources needed — only Gemini API)
AGENT_MOCK_GCP=true python demos/module1_demo.py

# Run specific section (1-6)
AGENT_MOCK_GCP=true python demos/module1_demo.py --section 4

# Run tests
AGENT_MOCK_GCP=true pytest tests/test_tools.py -v
```

### Module 2: Repository Analysis Agent

```bash
# Run demo in mock mode (no real repository needed)
AGENT_MOCK_REPO=true python demos/module2_demo.py

# Run specific section (1-11)
AGENT_MOCK_REPO=true python demos/module2_demo.py --section 5

# Run tests
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v
```

### Module 3: Terraform Generation Agent with Evaluation

```bash
# Run demo in mock mode (no GCP resources needed)
AGENT_MOCK_REPO=true python demos/module3_demo.py

# Run specific section (1-11)
AGENT_MOCK_REPO=true python demos/module3_demo.py --section 6

# Run Module 3 evaluation pipeline
AGENT_MOCK_REPO=true python -c "
from evaluation.pipelines.module3_eval import run_module3_evaluation
results = run_module3_evaluation(verbose=True)
print(f'Average Score: {results[\"summary\"][\"average_combined_score\"]:.1f}/100')
"

# Run tests
AGENT_MOCK_REPO=true pytest tests/test_module3_tools.py -v
AGENT_MOCK_REPO=true pytest tests/test_routing_agent.py -v
AGENT_MOCK_REPO=true pytest tests/test_evaluation.py -v
```

### Routing Agent

```bash
# Start routing agent server
python routing-agent/app.py

# Classify a request
curl -X POST http://localhost:8083/route \
  -H "Content-Type: application/json" \
  -d '{"request": "Analyze my repository at /home/user/app"}'

# Run tests
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v

# Start HTTP server
python module2/app.py
```

---

## Live Mode

### Module 1: GCP Prerequisites

**Gemini via Vertex AI (configured in gemini.yaml)**

1. GCP project with Vertex AI API enabled
2. Application Default Credentials: `gcloud auth application-default login`
3. Model configuration is in `gemini.yaml` (defaults to `gemini-2.5-pro` with ADC)

```bash
# Run against real GCP
python demos/module1_demo.py --live
```

**Model Garden (open-source alternative)**

1. *Google Cloud Console → Vertex AI → Model Garden*
2. Select a model (e.g. **Llama 3.1 8B** — no subscription fee)
3. Click **Deploy** → select machine type → wait for *"Deployed"*
4. Copy the endpoint ID
5. Set: `export MODEL_GARDEN_ENDPOINT="projects/.../endpoints/..."`

```bash
# Run with Model Garden model (same agent, different reasoning engine)
python demos/module1_demo.py --live --model-garden
```

### Modules 2-3: Prerequisites

**Gemini via Vertex AI** (all modules)

1. GCP project with Vertex AI API enabled
2. Application Default Credentials: `gcloud auth application-default login`
3. Model configuration in `gemini.yaml` (defaults to `gemini-2.5-pro`)

---

## Deploying Module 1 to Cloud Run

```bash
# 1. Test locally (no Docker needed)
AGENT_MOCK_GCP=true python module1/app.py
# → Serves on http://localhost:8080/invocations

# 2. Test the local server
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Give me a health summary of us-central1"}'

# 3. Deploy to Cloud Run
gcloud run deploy gcp-infra-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Tools Reference

All Module 1 tools are **read-only**. The only action path is `request_human_review`.

| Tool | Purpose | Slide Concept |
|---|---|---|
| `list_gcp_resources(service_type, region)` | Cloud Run / Compute / Cloud SQL / Functions listings | Grounding: agent sees current state |
| `describe_resource(service_type, name, region)` | Detailed drill-down | Multi-step reasoning |
| `check_resource_health(service_type, name, region)` | Structured health verdict | Observation |
| `get_environment_summary(region)` | Cross-service overview | Data synthesis |
| `request_human_review(...)` | Escalation ticket | Human-in-the-loop |

### Mock data

With `AGENT_MOCK_GCP=true` the tools return realistic simulated data including:
- **`api-gateway-svc`** → healthy (3/3 instances running on Cloud Run)
- **`notification-svc`** → degraded (1/2 instances, container crash) ← triggers HITL
- **`reporting-mysql`** → degraded (Cloud SQL, no HA, no failover)
- **`prod-postgres-01`** → healthy (Cloud SQL, HA enabled)

---

## The Model-Agnostic Property

The most important architectural property to highlight in the workshop:

```python
# config/models.py — reads from gemini.yaml

# Gemini via Vertex AI (default — configured in gemini.yaml)
model_id = get_vertex_model()

# Model Garden — open model via Vertex AI (ONE LINE change)
model_id = get_model_garden_model(endpoint_id="projects/.../endpoints/...")
```

The `create_agent()` factory in `agent.py` accepts `model_garden_endpoint` and swaps the model. **Tools, system prompt, session service, and Cloud Run wrapper are completely unchanged.**

---

## Multi-Agent Architecture (Future)

The agents are designed to work together in a multi-agent workflow:

```
┌─────────────────────────────────────────────────────────────┐
│  USER REQUEST: "Deploy this repository to the cloud"       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR (Module 4)                                    │
│  Coordinates agents to complete the task                    │
└─────────────────────────────────────────────────────────────┘
         ↓                                    ↓
┌──────────────────────┐          ┌──────────────────────────┐
│  MODULE 2 AGENT      │          │  MODULE 1 AGENT          │
│  (Repository)        │          │  (Infrastructure)        │
│                      │          │                          │
│  Analyzes repo:      │          │  Checks GCP:             │
│  • Apps detected     │   →→→    │  • Existing resources    │
│  • Stacks identified │          │  • Health status         │
│  • Infra needs mapped│   ←←←    │  • Gaps identified       │
└──────────────────────┘          └──────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  DEPLOYMENT PLAN                                            │
│  • Infrastructure to provision                              │
│  • Services to deploy (Cloud Run / Cloud Functions)         │
│  • Monitoring to configure (Cloud Monitoring)               │
└─────────────────────────────────────────────────────────────┘
```

**Example Workflow:**
1. Module 2 analyzes repository → identifies Node.js app needing PostgreSQL + Redis
2. Module 1 checks GCP → finds existing Cloud SQL PostgreSQL, no Memorystore Redis
3. Orchestrator generates plan → provision Memorystore, deploy app to Cloud Run
4. Human reviews and approves → infrastructure provisioned, app deployed

## What's Scoped Out (Future Modules)

| Capability | Module |
|---|---|
| Evaluation and routing patterns | Module 3 |
| Multi-agent supervisor pattern | Module 4 |
| Long-term memory (Firestore / vector store) | Module 7 |
| RAG / Knowledge Base | Module 10 |
| Production IAM hardening | Module 8 |
| Cloud Monitoring / Cloud Trace | Module 12 |

---

## Demo Sections

Run `AGENT_MOCK_GCP=true python demos/module1_demo.py --section N`:

| # | Title | Key Concept |
|---|---|---|
| 1 | Architecture anatomy | Three layers in code |
| 2 | The loop | Think → Act → Observe, live |
| 3 | Multi-step reasoning | Compound query, multiple tool calls |
| 4 | Human-in-the-loop | Agent escalates, doesn't act |
| 5 | Model swap | Gemini ↔ Model Garden |
| 6 | Context window | Multi-turn short-term memory |
