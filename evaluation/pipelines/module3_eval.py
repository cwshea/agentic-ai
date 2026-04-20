"""
evaluation/pipelines/module3_eval.py
=====================================
Evaluation pipeline for Module 3 Terraform Generation Agent.

Runs the agent against test cases and evaluates:
- Syntax Correctness: Valid Terraform HCL syntax
- Completeness: All required resources included
- Best Practices: Follows GCP and Terraform best practices
- Security: Proper security configurations
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from module3.evaluators.llm_judge import evaluate_with_llm_judge
from module3.evaluators.terraform_evaluator import evaluate_terraform_code
from evaluation.datasets.module3_testcases import MODULE3_TEST_CASES, MODULE3_EVALUATION_CRITERIA


def run_module3_evaluation(
    test_cases: list[dict[str, Any]] | None = None,
    agent_function: Any | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Run evaluation pipeline for Module 3 agent.

    Parameters
    ----------
    test_cases : list of dict, optional
        Test cases to evaluate. Defaults to MODULE3_TEST_CASES.
    agent_function : callable, optional
        Function to invoke the agent. If None, uses mock mode.
    verbose : bool
        Print evaluation progress.

    Returns
    -------
    dict
        Evaluation results with scores, pass/fail rates, and detailed results.
    """
    test_cases = test_cases or MODULE3_TEST_CASES
    mock_mode = agent_function is None

    if verbose:
        print(f"\n{'='*70}")
        print(f"  MODULE 3 EVALUATION PIPELINE")
        print(f"{'='*70}")
        print(f"  Test cases: {len(test_cases)}")
        print(f"  Mode: {'MOCK' if mock_mode else 'LIVE'}")
        print(f"  Criteria: {len(MODULE3_EVALUATION_CRITERIA)}")
        print(f"{'='*70}\n")

    results = []

    for i, test_case in enumerate(test_cases):
        if verbose:
            print(f"\n[Test Case {i+1}/{len(test_cases)}] {test_case['name']}")
            print(f"  Category: {test_case['category']}")

        if mock_mode:
            agent_output = _generate_mock_module3_output(test_case)
        else:
            try:
                agent_output = agent_function(test_case["input"])
            except Exception as e:
                agent_output = f"ERROR: {str(e)}"

        terraform_code = _extract_terraform_code(agent_output)

        tf_eval = evaluate_terraform_code(
            terraform_code=terraform_code,
            expected_resources=test_case["expected_output"].get("resources", []),
        )

        task_description = f"Generate Terraform infrastructure: {test_case['name']}\nRequirements: {json.dumps(test_case['input'], indent=2)}"

        llm_evaluation = evaluate_with_llm_judge(
            task_description=task_description,
            agent_output=terraform_code,
            criteria=MODULE3_EVALUATION_CRITERIA,
            reference_answer=f"Expected modules: {test_case['expected_output'].get('modules', [])}",
            verbose=verbose,
        )

        combined_score = int(
            (tf_eval.overall_score * 0.4)
            + (llm_evaluation.get("overall_score", 0) * 0.6)
        )

        result = {
            "test_case_id": test_case["id"],
            "test_case_name": test_case["name"],
            "category": test_case["category"],
            "terraform_code": terraform_code,
            "terraform_evaluation": tf_eval.to_dict(),
            "llm_evaluation": llm_evaluation,
            "combined_score": combined_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results.append(result)

        if verbose:
            print(f"  Terraform Score: {tf_eval.overall_score}/100")
            print(f"  LLM Score: {llm_evaluation.get('overall_score', 0)}/100")
            print(f"  Combined: {combined_score}/100")

    combined_scores = [r["combined_score"] for r in results]
    tf_scores = [r["terraform_evaluation"]["scores"]["overall"] for r in results]
    llm_scores = [r["llm_evaluation"].get("overall_score", 0) for r in results]

    criteria_scores = {}
    for criterion in MODULE3_EVALUATION_CRITERIA.keys():
        criterion_scores = [
            r["llm_evaluation"].get("scores", {}).get(criterion, 0)
            for r in results
        ]
        criteria_scores[criterion] = {
            "average": sum(criterion_scores) / len(criterion_scores) if criterion_scores else 0,
            "min": min(criterion_scores) if criterion_scores else 0,
            "max": max(criterion_scores) if criterion_scores else 0,
        }

    summary = {
        "total_test_cases": len(test_cases),
        "average_combined_score": sum(combined_scores) / len(combined_scores) if combined_scores else 0,
        "average_terraform_score": sum(tf_scores) / len(tf_scores) if tf_scores else 0,
        "average_llm_score": sum(llm_scores) / len(llm_scores) if llm_scores else 0,
        "pass_rate": sum(1 for s in combined_scores if s >= 70) / len(combined_scores) if combined_scores else 0,
        "syntax_valid_rate": sum(1 for r in results if r["terraform_evaluation"]["syntax_valid"]) / len(results) if results else 0,
        "criteria_scores": criteria_scores,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if verbose:
        print(f"\n{'='*70}")
        print(f"  EVALUATION SUMMARY")
        print(f"{'='*70}")
        print(f"  Average Combined Score: {summary['average_combined_score']:.1f}/100")
        print(f"  Average Terraform Score: {summary['average_terraform_score']:.1f}/100")
        print(f"  Average LLM Score: {summary['average_llm_score']:.1f}/100")
        print(f"  Pass Rate: {summary['pass_rate']*100:.1f}%")
        print(f"  Syntax Valid: {summary['syntax_valid_rate']*100:.1f}%")
        print(f"\n  Criteria Scores:")
        for criterion, stats in criteria_scores.items():
            print(f"    {criterion}: {stats['average']:.1f}/100")
        print(f"{'='*70}\n")

    return {
        "summary": summary,
        "results": results,
        "test_cases": test_cases,
    }


def _extract_terraform_code(output: Any) -> str:
    """Extract Terraform code from agent output."""
    if isinstance(output, dict):
        for key in ["terraform_code", "code", "output", "module"]:
            if key in output:
                return str(output[key])
        return str(output)
    return str(output)


def _generate_mock_module3_output(test_case: dict[str, Any]) -> str:
    """Generate mock Module 3 Terraform output for testing."""
    expected = test_case["expected_output"]

    mock_code = f'''# Mock Terraform module for {test_case['name']}

terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  project = var.project_id
  region  = var.region
}}

variable "project_id" {{
  description = "GCP project ID"
  type        = string
}}

variable "region" {{
  type    = string
  default = "us-central1"
}}

# Mock resources: {', '.join(expected.get('resources', []))}
# Expected modules: {', '.join(expected.get('modules', []))}
'''

    return mock_code
