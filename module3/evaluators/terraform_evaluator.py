"""
module3/evaluators/terraform_evaluator.py
==========================================
Terraform code quality evaluator.

Evaluates generated Terraform code for:
- Syntax correctness (HCL brace matching)
- Completeness (required resources present)
- Best practices (variables, outputs, naming)
- Security configurations (encryption, IAM, firewall)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TerraformEvaluationResult:
    """Result of Terraform code evaluation."""

    syntax_valid: bool
    syntax_errors: list[dict[str, Any]]
    completeness_score: int  # 0-100
    best_practices_score: int  # 0-100
    security_score: int  # 0-100
    overall_score: int  # 0-100
    issues: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "syntax_valid": self.syntax_valid,
            "syntax_errors": self.syntax_errors,
            "scores": {
                "completeness": self.completeness_score,
                "best_practices": self.best_practices_score,
                "security": self.security_score,
                "overall": self.overall_score,
            },
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


def evaluate_terraform_code(
    terraform_code: str,
    expected_resources: list[str] | None = None,
) -> TerraformEvaluationResult:
    """
    Evaluate Terraform code quality.

    Parameters
    ----------
    terraform_code : str
        Terraform HCL code to evaluate.
    expected_resources : list of str, optional
        List of expected GCP resources (e.g., ["google_compute_network", "google_sql_database_instance"]).

    Returns
    -------
    TerraformEvaluationResult
        Evaluation results with scores and recommendations.
    """
    issues = []
    recommendations = []

    # 1. Syntax validation (brace matching)
    syntax_valid = True
    syntax_errors = []
    brace_count = 0
    for i, line in enumerate(terraform_code.split("\n"), 1):
        brace_count += line.count("{") - line.count("}")
        if brace_count < 0:
            syntax_valid = False
            syntax_errors.append({"line": i, "message": "Unexpected closing brace"})

    if brace_count != 0:
        syntax_valid = False
        syntax_errors.append({"line": len(terraform_code.split("\n")), "message": f"Unmatched braces (balance: {brace_count})"})
        issues.append(f"Syntax error: unmatched braces")

    # 2. Completeness check
    completeness_score = 100

    required_blocks = ["resource", "provider"]
    for block in required_blocks:
        if block not in terraform_code:
            completeness_score -= 15
            issues.append(f"Missing required block: {block}")

    if expected_resources:
        for resource in expected_resources:
            if resource.lower() not in terraform_code.lower():
                completeness_score -= 10
                issues.append(f"Expected resource not found: {resource}")

    completeness_score = max(0, completeness_score)

    # 3. Best practices check
    best_practices_score = 100
    best_practices = {
        "variables": "variable" in terraform_code,
        "outputs": "output" in terraform_code,
        "provider_version": "required_providers" in terraform_code or "version" in terraform_code,
        "description": "description" in terraform_code,
    }

    for practice, present in best_practices.items():
        if not present:
            best_practices_score -= 15
            recommendations.append(f"Consider adding {practice.replace('_', ' ')}")

    best_practices_score = max(0, best_practices_score)

    # 4. Security check
    security_score = 100
    security_checks = {
        "encryption": "encrypt" in terraform_code.lower() or "kms" in terraform_code.lower(),
        "firewall": "firewall" in terraform_code.lower() or "private" in terraform_code.lower(),
        "iam": "service_account" in terraform_code.lower() or "iam" in terraform_code.lower(),
        "logging": "log" in terraform_code.lower() or "monitoring" in terraform_code.lower(),
    }

    for check, present in security_checks.items():
        if not present:
            security_score -= 20
            recommendations.append(f"Consider adding {check.replace('_', ' ')} configuration")

    if "public" in terraform_code.lower() and "prevention" not in terraform_code.lower():
        security_score -= 15
        issues.append("Potential public access — verify this is intentional")

    if "deletion_protection" in terraform_code.lower() and "false" in terraform_code.lower():
        security_score -= 10
        recommendations.append("Consider enabling deletion protection for production")

    security_score = max(0, security_score)

    # 5. Overall score
    if not syntax_valid:
        overall_score = 0
    else:
        overall_score = int(
            (completeness_score * 0.4)
            + (best_practices_score * 0.3)
            + (security_score * 0.3)
        )

    return TerraformEvaluationResult(
        syntax_valid=syntax_valid,
        syntax_errors=syntax_errors,
        completeness_score=completeness_score,
        best_practices_score=best_practices_score,
        security_score=security_score,
        overall_score=overall_score,
        issues=issues,
        recommendations=recommendations,
    )


def evaluate_terraform_batch(
    code_samples: list[dict[str, Any]],
) -> list[TerraformEvaluationResult]:
    """Evaluate multiple Terraform code samples."""
    return [
        evaluate_terraform_code(
            terraform_code=sample["code"],
            expected_resources=sample.get("expected_resources"),
        )
        for sample in code_samples
    ]
