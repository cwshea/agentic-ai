# Routing Agent: Intent Classification & Request Routing

Simple intent classification agent for routing requests to specialist agents.

## Overview

The routing agent classifies incoming user requests and routes them to the appropriate specialist agent (Module 1, Module 2, or Module 3). It uses a single LLM call for efficient classification without a full agent loop.

## Categories

| Category | Description | Target Agent | Port |
|----------|-------------|--------------|------|
| `repository_analysis` | Analyze software repositories | Module 2 | 8081 |
| `infrastructure_generation` | Generate Terraform infrastructure code for GCP | Module 3 | 8082 |
| `gcp_infrastructure` | Monitor and analyze existing GCP infrastructure | Module 1 | 8080 |
| `deployment_monitoring` | Deploy and monitor applications | Future | - |

## Quick Start

```bash
# Start routing agent server
python routing_agent/app.py

# Classify a request
curl -X POST http://localhost:8083/route \
  -H "Content-Type: application/json" \
  -d '{"request": "Analyze my repository at /home/user/app"}'

# Get available categories
curl http://localhost:8083/categories
```

## Usage

### Python API

```python
from routing_agent.agent import classify_intent, route_request

# Simple classification
result = classify_intent("Generate Terraform for a web app")
print(f"Category: {result['category']}")
print(f"Confidence: {result['confidence']}")
print(f"Target: {result['target_agent']}")

# Full routing with suggested action
routing = route_request("Analyze my repository")
print(f"Action: {routing['suggested_action']}")  # "route", "clarify", or "reject"
print(f"URL: {routing['target_url']}")
```

### Batch Classification

```python
from routing_agent.agent import classify_batch

requests = [
    "Analyze repository at /path/to/repo",
    "Generate Terraform for Cloud Run",
    "Check GCP health in us-central1",
]

results = classify_batch(requests)
for r in results:
    print(f"{r['category']}: {r['confidence']:.2f}")
```

## Classification Logic

### Confidence Thresholds

- **>= 0.7**: High confidence -> Route to target agent
- **0.5-0.7**: Medium confidence -> Ask clarifying questions
- **< 0.5**: Low confidence -> Reject or ask for rephrasing

### Example Classifications

```python
# High confidence - repository analysis
"Analyze the repository at /home/user/myapp"
# -> category: repository_analysis, confidence: 0.98

# High confidence - infrastructure generation
"Generate Terraform for a Node.js app with Cloud SQL"
# -> category: infrastructure_generation, confidence: 0.95

# Medium confidence - needs clarification
"Check my services"
# -> category: gcp_infrastructure, confidence: 0.65
# -> clarifying_questions: ["Which GCP services?", "What region?"]
```

## Architecture

### Model Configuration

- **Model**: Gemini via Vertex AI (from `gemini.yaml`)
- **Temperature**: 0.0 (deterministic classification)
- **Max Tokens**: 1024 (classification is short)
- **Framework**: LangChain (ChatGoogleGenerativeAI + StrOutputParser)

### No Agent Loop

Unlike Module 1, 2, and 3, the routing agent does NOT use a full agent loop. It's a single-shot classification:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTING_PROMPT),
    ("user", "{request}"),
])
chain = prompt | model | StrOutputParser()
response = chain.invoke({"request": user_request})
```

## Configuration

### Environment Variables

```bash
# Agent URLs (defaults shown)
MODULE1_URL=http://localhost:8080
MODULE2_URL=http://localhost:8081
MODULE3_URL=http://localhost:8082

# Routing agent server
ROUTING_PORT=8083
ROUTING_HOST=0.0.0.0
ROUTING_VERBOSE=false

# GCP
GOOGLE_CLOUD_PROJECT=your-project
GCP_REGION=us-central1
```

## Testing

```bash
AGENT_MOCK_REPO=true pytest tests/test_routing_agent.py -v
```

## Project Structure

```
routing_agent/
├── agent.py              # Classification and routing logic
├── app.py                # HTTP server
├── config/
│   └── models.py         # ChatGoogleGenerativeAI configuration
└── prompts/
    └── routing_prompts.py # Classification prompt and categories
```
