"""
tests/test_evaluation.py
=========================
Tests for evaluation system components.
"""

import os
import pytest

os.environ["AGENT_MOCK_REPO"] = "true"

from module3.evaluators.terraform_evaluator import evaluate_terraform_code, TerraformEvaluationResult
from module3.evaluators.llm_judge import evaluate_with_llm_judge
from evaluation.pipelines.module2_eval import run_module2_evaluation
from evaluation.pipelines.module3_eval import run_module3_evaluation
from evaluation.integrations.patronus_integration import PatronusEvaluator
from evaluation.integrations.deepchecks_integration import DeepchecksEvaluator
from evaluation.integrations.cometml_integration import CometMLTracker


def test_terraform_evaluator_valid_code():
    """Test Terraform evaluator with valid code."""
    code = '''
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

resource "google_compute_network" "vpc" {
  name                    = "main-vpc"
  auto_create_subnetworks = false
}
'''

    result = evaluate_terraform_code(code)

    assert isinstance(result, TerraformEvaluationResult)
    assert result.syntax_valid is True
    assert result.overall_score > 0


def test_terraform_evaluator_invalid_syntax():
    """Test Terraform evaluator with invalid syntax."""
    code = "resource broken { syntax here"

    result = evaluate_terraform_code(code)

    assert result.syntax_valid is False
    assert result.overall_score == 0


def test_terraform_evaluator_expected_resources():
    """Test Terraform evaluator with expected resources check."""
    code = '''
provider "google" {
  project = var.project_id
}

resource "google_compute_network" "vpc" {
  name = "test-vpc"
}
'''

    result = evaluate_terraform_code(code, expected_resources=["google_compute_network"])

    assert result.completeness_score > 0


def test_llm_judge_evaluation():
    """Test LLM-as-judge evaluation."""
    criteria = {
        "completeness": "All required elements present",
        "accuracy": "Technically correct",
    }

    result = evaluate_with_llm_judge(
        task_description="Generate VPC Terraform module",
        agent_output="Sample Terraform code",
        criteria=criteria,
        verbose=False,
    )

    assert "overall_score" in result
    assert "scores" in result


def test_module2_evaluation_pipeline():
    """Test Module 2 evaluation pipeline."""
    from evaluation.datasets.module2_testcases import MODULE2_TEST_CASES

    results = run_module2_evaluation(
        test_cases=MODULE2_TEST_CASES[:2],
        verbose=False,
    )

    assert "summary" in results
    assert "results" in results
    assert results["summary"]["total_test_cases"] == 2


def test_module3_evaluation_pipeline():
    """Test Module 3 evaluation pipeline."""
    from evaluation.datasets.module3_testcases import MODULE3_TEST_CASES

    results = run_module3_evaluation(
        test_cases=MODULE3_TEST_CASES[:2],
        verbose=False,
    )

    assert "summary" in results
    assert "results" in results
    assert results["summary"]["total_test_cases"] == 2


def test_patronus_evaluator_mock():
    """Test Patronus AI evaluator in mock mode."""
    evaluator = PatronusEvaluator()

    result = evaluator.evaluate(
        task="Test task",
        output="Test output",
        criteria={"quality": "High quality output"},
    )

    assert result["mock_mode"] is True
    assert "overall_score" in result
    assert "evaluation_id" in result


def test_patronus_regression_tracking():
    """Test Patronus regression tracking."""
    evaluator = PatronusEvaluator()

    eval_results = [
        {"overall_score": 85},
        {"overall_score": 90},
    ]

    result = evaluator.track_regression("v1.0", eval_results)

    assert result["agent_version"] == "v1.0"
    assert result["total_evaluations"] == 2


def test_deepchecks_hallucination_detection():
    """Test Deepchecks hallucination detection."""
    evaluator = DeepchecksEvaluator()

    output = "This will definitely always work perfectly."

    result = evaluator.detect_hallucinations(output)

    assert "hallucination_detected" in result
    assert "hallucination_score" in result


def test_deepchecks_quality_validation():
    """Test Deepchecks quality validation."""
    evaluator = DeepchecksEvaluator()

    output = "This is a reasonable output with good length and structure."

    result = evaluator.validate_output_quality(output)

    assert "quality_score" in result
    assert "issues" in result


def test_cometml_experiment_tracking():
    """Test Comet ML experiment tracking."""
    tracker = CometMLTracker()

    exp_id = tracker.start_experiment("test-experiment")

    assert exp_id is not None

    tracker.log_metrics({"accuracy": 0.95, "latency": 1.2})

    summary = tracker.end_experiment()

    assert "experiment_id" in summary


def test_cometml_anomaly_detection():
    """Test Comet ML anomaly detection."""
    tracker = CometMLTracker()

    tracker.start_experiment("anomaly-test")
    tracker.log_metrics({"score": 80})
    tracker.log_metrics({"score": 85})
    tracker.log_metrics({"score": 82})

    result = tracker.detect_anomalies("score")

    assert "anomalies_detected" in result
