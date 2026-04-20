# Getting Started with the AI Agent Learning Series

This guide helps you get started with both Module 1 and Module 2 agents.

## Prerequisites

- Python 3.11 or later
- GCP account with Vertex AI API enabled (for Module 1 live mode) or use mock mode for demos
- GCP project with Vertex AI API enabled (for live mode) or use mock mode for demos
- Git installed

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Module 1: GCP Infrastructure Agent

### Quick Demo (Mock Mode)

```bash
# Authenticate with GCP (required for Gemini model access)
gcloud auth application-default login

# Run the complete demo
AGENT_MOCK_GCP=true python demos/module1_demo.py

# Run specific sections
AGENT_MOCK_GCP=true python demos/module1_demo.py --section 1  # Architecture
AGENT_MOCK_GCP=true python demos/module1_demo.py --section 2  # The loop
AGENT_MOCK_GCP=true python demos/module1_demo.py --section 4  # Human-in-the-loop
```

### Live GCP Mode

```bash
# Authenticate with GCP
gcloud auth application-default login

# Ensure Vertex AI API is enabled in your project
# Google Cloud Console → APIs & Services → Enable Vertex AI API

# Run against real GCP
python demos/module1_demo.py --live
```

### Run Tests

```bash
AGENT_MOCK_GCP=true pytest tests/test_tools.py -v
```

## Module 2: Repository Analysis Agent

### Quick Demo (Mock Mode)

```bash
# Run the complete demo
AGENT_MOCK_REPO=true python demos/module2_demo.py

# Run specific sections
AGENT_MOCK_REPO=true python demos/module2_demo.py --section 1  # Framework comparison
AGENT_MOCK_REPO=true python demos/module2_demo.py --section 3  # App detection
AGENT_MOCK_REPO=true python demos/module2_demo.py --section 6  # Full workflow
```

### Analyze a Real Repository

```bash
# Analyze any git repository
python demos/module2_demo.py --repo /path/to/your/repo
```

### Run Tests

```bash
AGENT_MOCK_REPO=true pytest tests/test_repo_tools.py -v
```

### Start HTTP Server

```bash
# Start the server (port 8081)
python module2/app.py

# In another terminal, test it
curl -X POST http://localhost:8081/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/repo"}'
```

## Using Both Agents Together (Python API)

```python
# Module 1: Check GCP infrastructure
from module1.agent import create_agent as create_infra_agent

infra_agent = create_infra_agent(verbose=True)
gcp_status = infra_agent("Give me a health summary of us-central1")
print(gcp_status)

# Module 2: Analyze repository
from module2.agent import analyze_repository

repo_analysis = analyze_repository("/path/to/repo", verbose=True)
print(repo_analysis["analysis"])

# Future: Orchestrator will coordinate both agents
```

## LangSmith Tracing (Module 2)

Enable detailed tracing for Module 2:

```bash
# Set environment variables
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your-langsmith-api-key
export LANGCHAIN_PROJECT=repo-analysis-agent

# Run demo - traces appear in LangSmith dashboard
python demos/module2_demo.py
```

View traces at: https://smith.langchain.com/

## Common Issues

### Import Errors

If you see import errors, ensure you're in the virtual environment and have installed dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### GCP Credentials Not Found (Module 1)

The agent needs Gemini API access via Vertex AI. Authenticate with:
```bash
gcloud auth application-default login
```

Use mock mode for infrastructure tools (still requires Gemini for reasoning):
```bash
AGENT_MOCK_GCP=true python demos/module1_demo.py
```

### Repository Not Found (Module 2)

Use mock mode for demos:
```bash
AGENT_MOCK_REPO=true python demos/module2_demo.py
```

Or provide a valid git repository path:
```bash
python demos/module2_demo.py --repo /path/to/valid/git/repo
```

## Next Steps

1. **Run both demos** to see the agents in action
2. **Read the module READMEs** for detailed documentation
3. **Explore the code** to understand the implementation
4. **Try with real data** (GCP project or git repositories)
5. **Wait for Module 3** for evaluation and routing patterns
6. **Wait for Module 4** for multi-agent orchestration

## Learning Path

1. **Module 1 Demo** → Understand agent fundamentals (Google ADK framework)
2. **Module 2 Demo** → Learn LangChain/LangGraph approach
3. **Compare frameworks** → See different ways to build the same patterns
4. **Run tests** → Understand tool implementation
5. **Modify agents** → Experiment with your own use cases

## Resources

- [Module 1 README](module1/README.md)
- [Module 2 README](module2/README.md)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Vertex AI](https://cloud.google.com/vertex-ai)
