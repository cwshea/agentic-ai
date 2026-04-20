# Module 3 Architecture Documentation

## Overview

Module 3 demonstrates Terraform infrastructure generation and agent evaluation patterns. This document clarifies the actual implementation behavior.

## Terraform Generation Tools - Important Clarification

### Current Implementation: Template-Based Generation

**The Terraform generation tools do NOT use LLM models to generate code.** Instead, they use pre-defined Python templates that generate Terraform code based on parameters.

#### How It Works

1. **User Request**: "Generate Terraform for a VPC with 2 AZs"
2. **Tool Called**: `generate_terraform_module(stack_type="vpc", parameters='{"max_azs": 2}')`
3. **Code Generation**: Python function `generate_vpc_stack()` returns a string template
4. **No LLM Involved**: The code is generated from a template, not by Claude

#### Why Sections 1-6 Run Instantly

Sections 1-6 of the demo run instantly because:
- No LLM API calls are made
- Code is generated from Python string templates
- Only template substitution happens (e.g., replacing `max_azs` parameter)
- This is true **regardless** of `AGENT_MOCK_REPO` setting

#### Mock Mode vs Real Mode

The `AGENT_MOCK_REPO` environment variable **only affects**:
- The JSON wrapper metadata (`"mock_mode": true/false`)
- Whether Module 2 repository analysis tools call real file system operations
- Whether evaluation components call real Vertex AI APIs

The `AGENT_MOCK_REPO` variable **does NOT affect**:
- Terraform code generation (always template-based)
- Speed of sections 1-6 (always instant)
- The actual Terraform code output (same templates used)

### Template Functions

The following template functions generate Terraform code:

```python
# module3/tools/terraform_tools.py

def generate_vpc_stack(max_azs: int, nat_gateways: int) -> str:
    """Returns VPC Terraform code as a string template"""
    
def generate_ecs_stack(service_name: str, ...) -> str:
    """Returns Cloud Run Terraform code as a string template"""
    
def generate_rds_stack(engine: str, ...) -> str:
    """Returns Cloud SQL Terraform code as a string template"""
    
# ... etc for elasticache, s3, lambda
```

These are **not** LLM-generated. They are Python functions that return formatted strings.

## What Actually Uses LLMs

### Components That Call Vertex AI APIs

1. **LLM-as-Judge Evaluator** (`module3/evaluators/llm_judge.py`)
   - Uses Claude Opus 4 for evaluation
   - Only runs in Section 6 and evaluation pipelines
   - Respects `AGENT_MOCK_REPO` for mock mode

2. **Routing Agent** (`routing_agent/agent.py`)
   - Uses Claude Sonnet 4 for intent classification
   - Only runs in Section 9
   - Respects `AGENT_MOCK_REPO` for mock mode

3. **Module 2 Repository Analysis** (if used)
   - Uses Claude Sonnet 4 for code analysis
   - Not part of Module 3 demo sections 1-6

### Components That Use ISV APIs

1. **Patronus AI** - Real mode requires `PATRONUS_API_KEY`
2. **Deepchecks** - Real mode requires `DEEPCHECKS_API_KEY`
3. **Comet ML** - Real mode requires `COMET_API_KEY`

## Design Rationale

### Why Template-Based Generation?

The template-based approach was chosen for:

1. **Reliability**: Guaranteed syntactically correct Terraform code
2. **Best Practices**: Templates encode GCP best practices
3. **Demo Speed**: Instant execution for workshops
4. **Cost**: No Vertex AI API costs for basic demos
5. **Offline**: Works without GCP credentials

### When Would You Use LLM Generation?

In a production system, you might use LLM generation for:

- **Custom Requirements**: Complex, unique infrastructure needs
- **Natural Language**: Converting prose descriptions to code
- **Adaptation**: Modifying existing infrastructure
- **Learning**: Explaining infrastructure decisions

However, for standard patterns (VPC, Cloud Run, Cloud SQL), templates are often more reliable and faster.

## Running the Demo

### Mock Mode (Default for Sections 1-6)

```bash
# Sections 1-6 always run instantly (template-based)
python demos/module3_demo.py

# Explicitly set mock mode for evaluation sections
AGENT_MOCK_REPO=true python demos/module3_demo.py
```

### Real Mode (For Evaluation Components)

```bash
# Sections 1-6 still instant (templates)
# Sections 5-6 will call real Vertex AI APIs for evaluation
python demos/module3_demo.py
# Requires GCP credentials configured
```

### ISV Integrations (Sections 7-9)

```bash
# Set API keys for real ISV integrations
export PATRONUS_API_KEY="your-key"
export COMET_API_KEY="your-key"
# DEEPCHECKS_API_KEY optional (may not have free tier)

python demos/module3_demo.py
```

## Summary

| Component | Uses LLM? | Uses Templates? | Respects AGENT_MOCK_REPO? |
|-----------|-----------|-----------------|---------------------------|
| Terraform Generation (Sections 1-4) | ❌ No | ✅ Yes | ❌ No (always templates) |
| Evaluation Pipeline (Section 5) | ✅ Yes (Judge) | ❌ No | ✅ Yes |
| LLM-as-Judge (Section 6) | ✅ Yes | ❌ No | ✅ Yes |
| Patronus AI (Section 7) | ❌ No (ISV API) | ❌ No | Uses PATRONUS_API_KEY |
| Deepchecks (Section 8) | ❌ No (ISV API) | ❌ No | Uses DEEPCHECKS_API_KEY |
| Routing Agent (Section 9) | ✅ Yes | ❌ No | ✅ Yes |
| Comet ML (Section 10) | ❌ No (ISV API) | ❌ No | Uses COMET_API_KEY |

## Future Enhancements

To add true LLM-based Terraform generation:

1. Create a new tool that calls Claude with Terraform generation prompts
2. Use the existing templates as few-shot examples
3. Add validation and safety checks on LLM output
4. Implement retry logic for malformed code
5. Cache successful patterns to reduce API calls

This would make the system more flexible but slower and more expensive.
