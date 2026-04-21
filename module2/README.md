# Module 2: Repository Analysis Agent

LangChain-based agent for analyzing git repositories to identify applications, technology stacks, and GCP infrastructure requirements.

## Overview

This module demonstrates the **Module 2 framework approach** using LangChain and LangGraph, complementing the Module 1 GCP Infrastructure Agent (Google ADK-based). Together, they form the foundation for multi-agent DevOps automation.

## What This Agent Does

1. **Scans** local git repositories to understand structure
2. **Detects** distinct applications/services (monorepo support)
3. **Analyzes** technology stacks (languages, frameworks, dependencies)
4. **Maps** dependencies to GCP infrastructure requirements
5. **Generates** structured analysis reports for deployment planning

## Quick Start

```bash
# Mock mode (no real repository needed)
AGENT_MOCK_REPO=true python demos/module2_demo.py

# Analyze a real repository
python demos/module2_demo.py --repo /path/to/your/repo

# Run specific demo section
AGENT_MOCK_REPO=true python demos/module2_demo.py --section 4

# Run tests
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v
```

## Architecture

### Framework: LangChain + LangGraph

**Model Interface**: `ChatGoogleGenerativeAI` (Gemini via Vertex AI)
**Execution Loop**: `AgentExecutor` or LangGraph state machine
**Tools**: 5 repository analysis tools
**Observability**: LangSmith tracing integration

### Five Repository Analysis Tools

1. **`scan_repository_structure`** - List files/directories with git awareness
2. **`read_file_content`** - Read specific files (package.json, requirements.txt, etc.)
3. **`detect_applications`** - Identify distinct apps/services in repository
4. **`analyze_dependencies`** - Parse dependency files and extract libraries
5. **`map_gcp_services`** - Map dependencies to GCP services (Cloud SQL, Memorystore, etc.)

## Framework Comparison: Module 1 vs Module 2

| Aspect | Module 1 (Google ADK) | Module 2 (LangChain) |
|--------|----------------------|---------------------|
| **Framework** | Google ADK | LangChain + LangGraph |
| **Model Interface** | Gemini via Vertex AI | `ChatGoogleGenerativeAI` |
| **Agent Pattern** | ADK `Agent` + `Runner` | `AgentExecutor` or LangGraph |
| **Memory** | `InMemorySessionService` | `ConversationBufferMemory` |
| **Observability** | Event callbacks | LangSmith tracing |
| **Use Case** | GCP infrastructure management | Repository analysis |
| **Tools** | GCP API calls (Cloud Run, GCE, Cloud SQL) | Local git operations |

Both implement the think-act-observe loop with different model providers.

## Example Output

```json
{
  "repository": "/path/to/repo",
  "applications": [
    {
      "name": "api-service",
      "path": "services/api",
      "stack": {
        "language": "Node.js",
        "runtime": "18.x",
        "framework": "Express",
        "dependencies": ["pg", "redis", "@google-cloud/storage"]
      },
      "gcp_requirements": {
        "compute": "Cloud Run or Cloud Functions",
        "database": "Cloud SQL PostgreSQL",
        "cache": "Memorystore Redis",
        "storage": "Cloud Storage",
        "networking": "VPC, Cloud Load Balancing"
      }
    }
  ],
  "summary": {
    "total_applications": 1,
    "languages": ["Node.js"],
    "gcp_services_needed": ["Cloud Run", "Cloud SQL", "Memorystore", "Cloud Storage", "VPC", "Cloud Load Balancing"]
  }
}
```

## Usage

### Python API

```python
from module2.agent import create_agent, analyze_repository

# Simple approach
agent = create_agent(verbose=True)
result = agent.invoke({"input": "Analyze repository at /path/to/repo"})
print(result["output"])

# Convenience function
results = analyze_repository("/path/to/repo")
print(results["analysis"])
```

### HTTP Server

```bash
# Start server
python module2/app.py

# Analyze repository
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo"}'
```

## LangSmith Tracing

Enable LangSmith for detailed observability:

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-key>
export LANGCHAIN_PROJECT=repo-analysis-agent

python demos/module2_demo.py
```

View traces at: https://smith.langchain.com/

## Dependency Mapping

The agent maps common libraries to GCP services:

| Dependency | GCP Service | Engine |
|------------|-------------|--------|
| `pg`, `psycopg2` | Cloud SQL | PostgreSQL |
| `mysql`, `mysql2` | Cloud SQL | MySQL |
| `mongodb`, `pymongo` | Firestore | Document DB |
| `redis`, `ioredis` | Memorystore | Redis |
| `google-cloud-storage` | Cloud Storage | Object Storage |
| `celery` | Cloud Tasks | Task Queue |
| `express`, `fastapi` | Cloud Run / Cloud Functions | Web Framework |

See `module2/tools/repo_tools.py` for the complete mapping.

## Multi-Agent Integration (Future)

Module 2 is designed to work with Module 1 in a multi-agent workflow:

1. **Module 2 Agent** analyzes repository → identifies infrastructure needs
2. **Module 1 Agent** checks existing GCP resources → identifies gaps
3. **Module 3 Agent** generates Terraform infrastructure code
4. **Orchestrator** (Module 4) coordinates all agents → generates deployment plan

This multi-agent pattern will be covered in Module 4.

## Project Structure

```
module2/
├── agent.py              # Agent factory and main logic
├── app.py                # HTTP server entrypoint
├── config/
│   └── models.py         # ChatGoogleGenerativeAI configuration
├── tools/
│   └── repo_tools.py     # 5 repository analysis tools
├── workflows/
│   └── analysis_graph.py # LangGraph state machine
└── prompts/
    └── system_prompts.py # System prompts for each stage
```

## Testing

```bash
# Run all tests
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v

# Run specific test
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py::test_scan_repository_structure_mock -v

# Test with real repository (requires git repo)
pytest tests/test_repo_tools.py::test_full_analysis_workflow -v
```

## Tool Comparison: Google ADK vs LangChain

| Aspect | Google ADK (Module 1) | LangChain (Module 2) |
|--------|----------------------|---------------------|
| Definition | Plain function with type hints | `@tool` decorator |
| Parameters | Inferred from signature | Inferred from signature |
| Description | Docstring | Docstring |
| Return Type | Any (dict or str) | String (JSON) |
| Registration | Pass list to `Agent()` | Pass list to `create_react_agent()` |
| Invocation | Automatic via ADK Runner | Automatic via LangGraph |

Both frameworks use the same pattern: define tools as functions, collect them in a list, and pass to the agent. The agent autonomously decides which tools to call via the ReAct (Think → Act → Observe) loop.

## Demo Sections

Run `AGENT_MOCK_REPO=true python demos/module2_demo.py --section N`:

| # | Title | Key Concept |
|---|-------|-------------|
| 1 | Framework comparison | LangChain vs Google ADK architecture |
| 2 | Agent identity | System prompts and agent persona |
| 3 | Context management | Conversation history across frameworks |
| 4 | Chains | Composable workflows with LCEL |
| 5 | Tools in LangChain | Tool definition, registration, ReAct loop |
| 6 | Tools comparison | LangChain vs Google ADK tool patterns |
| 7 | Repository scan | File structure analysis |
| 8 | Application detection | Multi-app/monorepo identification |
| 9 | Dependency analysis | Stack and GCP service mapping |
| 10 | LangSmith tracing | Observability and debugging |
| 11 | Full workflow | Complete analysis pipeline |

## Next Steps

- **Module 3**: Evaluation and routing patterns
- **Module 4**: Multi-agent orchestration (Module 1 + Module 2 working together)
- **Module 7**: Long-term memory with Firestore and vector stores

## License

Part of the AI Agent Learning Series.
