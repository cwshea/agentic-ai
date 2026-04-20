# Module 3: Terraform Infrastructure Generation Agent

LangChain-based agent for generating GCP Terraform infrastructure code from repository analysis or direct requirements.

## Overview

Module 3 demonstrates **evaluation and decision engines** using LangChain and LangGraph. It generates production-ready Terraform configurations for GCP based on infrastructure requirements, with comprehensive evaluation and quality assurance.

## What This Agent Does

1. **Analyzes** infrastructure requirements from Module 2 output or user specifications
2. **Clarifies** deployment preferences through targeted questions
3. **Generates** production-ready Terraform HCL code following GCP best practices
4. **Validates** generated code for syntax correctness and security
5. **Evaluates** output quality using LLM-as-judge and automated checks

## Quick Start

```bash
# Mock mode (no GCP resources needed — only Gemini API)
AGENT_MOCK_REPO=true python demos/module3_demo.py

# Run specific demo section
AGENT_MOCK_REPO=true python demos/module3_demo.py --section 6

# Run tests
AGENT_MOCK_REPO=true pytest tests/test_module3_tools.py -v
```

## Architecture

### Framework: LangChain + LangGraph

**Model Interface**: `ChatGoogleGenerativeAI` (Gemini via Vertex AI)
**Execution Loop**: LangGraph ReAct agent pattern
**Tools**: 5 Terraform generation and validation tools
**Observability**: LangSmith tracing integration

### Five Terraform Generation Tools

1. **`analyze_infrastructure_requirements`** - Parse Module 2 output or requirements
2. **`generate_terraform_module`** - Generate Terraform HCL for GCP services
3. **`validate_terraform_syntax`** - Validate generated Terraform syntax
4. **`list_available_resources`** - List available GCP Terraform resources
5. **`generate_terraform_tests`** - Generate test configurations for modules

## Supported Infrastructure Patterns

- **Network**: VPC with public/private subnets and Cloud NAT
- **Cloud Run**: Container service with VPC connector and scaling
- **Cloud SQL**: HA database with encryption and backups
- **Memorystore**: Redis instance with replication and encryption
- **Cloud Storage**: Encrypted buckets with versioning and lifecycle rules
- **Cloud Functions**: 2nd gen functions with VPC connector

## Example Output

```hcl
resource "google_sql_database_instance" "app_db" {
  name             = "app-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-custom-2-8192"
    availability_type = "REGIONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = true
}
```

## Usage

### Python API

```python
from module3.agent import create_agent, generate_infrastructure

# Simple approach
agent = create_agent(verbose=True)
result = agent.invoke({
    "messages": [("user", "Generate Terraform for web app with Cloud SQL")]
})
print(result["messages"][-1].content)

# Convenience function
requirements = {
    "compute": "Cloud Run",
    "database": "Cloud SQL PostgreSQL",
    "cache": "Memorystore Redis",
}
results = generate_infrastructure(requirements, region="us-central1")
print(results["output"])
```

### HTTP Server

```bash
# Start server
python module3/app.py

# Generate infrastructure
curl -X POST http://localhost:8082/generate \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {
      "compute": "Cloud Run",
      "database": "Cloud SQL PostgreSQL"
    },
    "region": "us-central1",
    "environment": "prod"
  }'

# Validate Terraform code
curl -X POST http://localhost:8082/validate \
  -H "Content-Type: application/json" \
  -d '{"terraform_code": "resource \"google_compute_network\" \"vpc\" { ... }"}'
```

## Evaluation System

### Four Evaluation Dimensions

1. **Syntax Correctness**: Valid Terraform HCL syntax (pass/fail)
2. **Completeness**: All required resources included (0-100%)
3. **Best Practices**: Follows GCP and Terraform best practices (0-100%)
4. **Security**: Proper encryption, IAM, firewall rules (0-100%)

### LLM-as-Judge Pattern

```python
from module3.evaluators.llm_judge import evaluate_with_llm_judge

criteria = {
    "completeness": "All required Terraform resources are included",
    "best_practices": "Follows GCP and Terraform best practices",
    "security": "Proper security configurations",
}

result = evaluate_with_llm_judge(
    task_description="Generate VPC Terraform module",
    agent_output=terraform_code,
    criteria=criteria,
)

print(f"Overall Score: {result['overall_score']}/100")
```

## Integration with Module 2

Module 3 works seamlessly with Module 2's repository analysis:

```python
# Module 2: Analyze repository
from module2.agent import analyze_repository

repo_analysis = analyze_repository("/path/to/repo")

# Module 3: Generate infrastructure from analysis
from module3.agent import generate_infrastructure

terraform = generate_infrastructure(
    requirements=repo_analysis["output"],
    region="us-central1",
    environment="prod",
)
```

## Project Structure

```
module3/
├── agent.py              # Agent factory and main logic
├── app.py                # HTTP server entrypoint
├── config/
│   └── models.py         # ChatGoogleGenerativeAI configuration
├── tools/
│   └── terraform_tools.py # 5 Terraform generation tools
├── templates/
│   └── terraform_modules.py # Reusable Terraform HCL templates
├── prompts/
│   └── system_prompts.py # System prompts for generation
└── evaluators/
    ├── llm_judge.py      # LLM-as-judge implementation
    └── terraform_evaluator.py # Terraform code quality evaluator
```

## Testing

```bash
# Run all Module 3 tests
AGENT_MOCK_REPO=true pytest tests/test_module3_tools.py -v

# Run evaluation tests
AGENT_MOCK_REPO=true pytest tests/test_evaluation.py -v
```

## Demo Sections

Run `AGENT_MOCK_REPO=true python demos/module3_demo.py --section N`:

| # | Title | Key Concept |
|---|-------|-------------|
| 1 | Framework consistency | LangChain across Module 2 & 3 |
| 2 | Terraform generation | Simple web app infrastructure |
| 3 | Interactive questions | Agent asks clarifying questions |
| 4 | Complex infrastructure | Multi-service microservices stack |
| 5 | Evaluation pipeline | Running Module 2 evaluation |
| 6 | LLM-as-judge | Automated quality scoring |
| 7 | Patronus AI | Custom evaluation criteria |
| 8 | Deepchecks | Hallucination detection |
| 9 | Routing agent | Intent classification demo |
| 10 | Self-correction | Agent evaluates and revises output |
| 11 | Full workflow | Module 2 → Module 3 → Evaluation |

## Best Practices

### Terraform Code Generation

- **Regional (HA) deployments** for production workloads
- **Encryption at rest and in transit** for all data stores
- **Service accounts** with least privilege IAM roles
- **Firewall rules** with minimal necessary access
- **Cloud Monitoring** alerts and logging
- **Proper labeling** for cost allocation

## Next Steps

- **Module 4**: Multi-agent orchestration (Module 1 + Module 2 + Module 3)
- **Module 7**: Long-term memory with Firestore and vector stores
- **Module 12**: Production monitoring with Cloud Monitoring and Cloud Trace
