"""
module3/tools/terraform_tools.py
=================================
Terraform generation and validation tools for Module 3.

These tools enable the agent to:
1. Parse infrastructure requirements from Module 2 output
2. Generate Terraform module code for GCP services
3. Validate generated Terraform syntax
4. List available Terraform resources
5. Generate test files for Terraform modules
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

from module3.templates.terraform_modules import (
    generate_network_module,
    generate_cloud_run_module,
    generate_cloud_sql_module,
    generate_memorystore_module,
    generate_gcs_module,
    generate_cloud_functions_module,
)

_MOCK = os.getenv("AGENT_MOCK_REPO", "false").lower() == "true"


def _wrap(data: Any, tool_name: str) -> str:
    """Wrap tool output in consistent JSON envelope."""
    return json.dumps(
        {
            "tool": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mock_mode": _MOCK,
            "data": data,
        },
        indent=2,
        default=str,
    )


def _validate_terraform_syntax(code: str) -> dict[str, Any]:
    """Basic Terraform HCL syntax validation."""
    errors = []
    brace_count = 0
    for i, line in enumerate(code.split("\n"), 1):
        brace_count += line.count("{") - line.count("}")
        if brace_count < 0:
            errors.append({"line": i, "message": "Unexpected closing brace"})

    if brace_count != 0:
        errors.append({"line": len(code.split("\n")), "message": f"Unmatched braces (balance: {brace_count})"})

    has_resource = "resource" in code or "variable" in code or "provider" in code
    if not has_resource:
        errors.append({"line": 1, "message": "No resource, variable, or provider blocks found"})

    return {"valid": len(errors) == 0, "errors": errors}


MOCK_MODULE2_OUTPUT = {
    "repository": "/mock/repo/nodejs-app",
    "applications": [
        {
            "name": "api-service",
            "path": "services/api",
            "stack": {
                "language": "Node.js",
                "runtime": "18.x",
                "framework": "Express",
                "dependencies": ["pg", "redis", "@google-cloud/storage"],
            },
            "gcp_requirements": {
                "compute": "Cloud Run",
                "database": "Cloud SQL PostgreSQL",
                "cache": "Memorystore Redis",
                "storage": "Cloud Storage",
                "networking": "VPC, Cloud Load Balancing",
            },
        }
    ],
    "summary": {
        "total_applications": 1,
        "languages": ["Node.js"],
        "gcp_services_needed": ["Cloud Run", "Cloud SQL", "Memorystore", "Cloud Storage", "VPC", "Cloud Load Balancing"],
    },
}


@tool
def analyze_infrastructure_requirements(requirements: str) -> str:
    """
    Parse infrastructure requirements from Module 2 output or user specifications.

    Extracts required GCP services (compute, database, cache, storage),
    technology stack details, deployment patterns, and networking requirements.

    Args:
        requirements: JSON string from Module 2 or plain text requirements

    Returns:
        JSON string with parsed requirements and recommended Terraform modules
    """
    if _MOCK:
        result = {
            "parsed_requirements": {
                "compute": {
                    "type": "Cloud Run",
                    "container_port": 8080,
                    "min_instances": 1,
                    "max_instances": 10,
                    "cpu": "1",
                    "memory": "512Mi",
                },
                "database": {
                    "type": "Cloud SQL PostgreSQL",
                    "version": "POSTGRES_15",
                    "tier": "db-custom-2-8192",
                    "high_availability": True,
                },
                "cache": {
                    "type": "Memorystore Redis",
                    "redis_version": "7_0",
                    "memory_size_gb": 1,
                },
                "storage": {
                    "type": "Cloud Storage",
                    "versioned": True,
                },
                "networking": {
                    "vpc": True,
                    "load_balancer": "Cloud Load Balancing",
                },
            },
            "recommended_modules": [
                "network - VPC with public/private subnets and Cloud NAT",
                "cloud_sql - PostgreSQL database with HA",
                "memorystore - Redis cache with replication",
                "gcs - Cloud Storage bucket with versioning",
                "cloud_run - Container service with VPC connector",
            ],
            "questions_needed": [
                "What GCP project should this be deployed to?",
                "What environment is this for (dev/staging/prod)?",
                "Do you need deletion protection on the database?",
            ],
        }
        return _wrap(result, "analyze_infrastructure_requirements")

    try:
        req_data = json.loads(requirements)
        gcp_reqs = {}
        if "applications" in req_data and req_data["applications"]:
            app = req_data["applications"][0]
            gcp_reqs = app.get("gcp_requirements", {})

        parsed = {
            "parsed_requirements": gcp_reqs,
            "recommended_modules": [],
            "questions_needed": [
                "What GCP project should this be deployed to?",
                "What environment is this for (dev/staging/prod)?",
            ],
        }
        return _wrap(parsed, "analyze_infrastructure_requirements")

    except json.JSONDecodeError:
        result = {
            "parsed_requirements": {"raw_text": requirements},
            "recommended_modules": [],
            "questions_needed": [
                "Please provide more specific details about required GCP services",
            ],
        }
        return _wrap(result, "analyze_infrastructure_requirements")


@tool
def generate_terraform_module(
    module_type: str,
    parameters: str,
) -> str:
    """
    Generate Terraform module code for a specific GCP service.

    Supported module types:
    - network: VPC with subnets and Cloud NAT
    - cloud_run: Cloud Run service with VPC connector
    - cloud_sql: Cloud SQL database (PostgreSQL, MySQL)
    - memorystore: Memorystore Redis instance
    - gcs: Cloud Storage bucket with encryption
    - cloud_functions: Cloud Functions (2nd gen)

    Args:
        module_type: Type of module to generate (network, cloud_run, cloud_sql, memorystore, gcs, cloud_functions)
        parameters: JSON string with module-specific parameters

    Returns:
        JSON string with generated Terraform code and metadata
    """
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        params = {}

    module_type = module_type.lower()

    generators = {
        "network": lambda p: generate_network_module(vpc_name=p.get("vpc_name", "main")),
        "cloud_run": lambda p: generate_cloud_run_module(
            service_name=p.get("service_name", "app"),
            image=p.get("image", "gcr.io/project/app:latest"),
            container_port=p.get("container_port", 8080),
            cpu=p.get("cpu", "1"),
            memory=p.get("memory", "512Mi"),
            min_instances=p.get("min_instances", 1),
            max_instances=p.get("max_instances", 10),
        ),
        "cloud_sql": lambda p: generate_cloud_sql_module(
            db_name=p.get("db_name", "app-db"),
            database_version=p.get("database_version", "POSTGRES_15"),
            tier=p.get("tier", "db-custom-2-8192"),
            availability_type=p.get("availability_type", "REGIONAL"),
            disk_size=p.get("disk_size", 20),
            backup_retention=p.get("backup_retention", 7),
            deletion_protection=p.get("deletion_protection", True),
        ),
        "memorystore": lambda p: generate_memorystore_module(
            cache_name=p.get("cache_name", "redis-cache"),
            tier=p.get("tier", "STANDARD_HA"),
            memory_size_gb=p.get("memory_size_gb", 1),
            redis_version=p.get("redis_version", "7_0"),
        ),
        "gcs": lambda p: generate_gcs_module(
            bucket_name=p.get("bucket_name", "app-bucket"),
            versioned=p.get("versioned", True),
        ),
        "cloud_functions": lambda p: generate_cloud_functions_module(
            function_name=p.get("function_name", "my-function"),
            runtime=p.get("runtime", "python312"),
            entry_point=p.get("entry_point", "main"),
            memory=p.get("memory", 256),
            timeout=p.get("timeout", 60),
        ),
    }

    if module_type not in generators:
        return _wrap(
            {"error": f"Unknown module type: {module_type}", "supported_types": list(generators.keys())},
            "generate_terraform_module",
        )

    code = generators[module_type](params)
    validation = _validate_terraform_syntax(code)

    result = {
        "module_type": module_type,
        "parameters": params,
        "code": code,
        "syntax_valid": validation["valid"],
        "syntax_errors": validation["errors"],
        "required_providers": ["hashicorp/google ~> 5.0"],
        "deployment_command": "terraform init && terraform plan && terraform apply",
    }

    return _wrap(result, "generate_terraform_module")


@tool
def validate_terraform_syntax(terraform_code: str) -> str:
    """
    Validate Terraform code for syntax errors and best practices.

    Checks:
    - HCL syntax validity (brace matching)
    - Required blocks present (provider, resource)
    - GCP best practices
    - Security configurations

    Args:
        terraform_code: Terraform HCL code to validate

    Returns:
        JSON string with validation results
    """
    syntax_check = _validate_terraform_syntax(terraform_code)

    required_blocks = ["resource", "provider"]
    if "terraform" not in terraform_code and "module" not in terraform_code:
        required_blocks.append("terraform")

    missing_blocks = [b for b in required_blocks if b not in terraform_code]

    best_practice_checks = {
        "encryption": "encrypt" in terraform_code.lower() or "kms" in terraform_code.lower(),
        "firewall": "firewall" in terraform_code.lower() or "private" in terraform_code.lower(),
        "iam": "service_account" in terraform_code.lower() or "iam" in terraform_code.lower(),
        "logging": "log" in terraform_code.lower() or "monitoring" in terraform_code.lower(),
        "variables": "variable" in terraform_code,
    }

    issues = []
    if not best_practice_checks["encryption"]:
        issues.append("Consider enabling encryption for data at rest")
    if not best_practice_checks["firewall"]:
        issues.append("Consider adding firewall rules or private networking")

    result = {
        "status": "PASS" if syntax_check["valid"] and not missing_blocks else "FAIL",
        "syntax": {
            "valid": syntax_check["valid"],
            "errors": syntax_check["errors"],
        },
        "blocks": {
            "complete": len(missing_blocks) == 0,
            "missing": missing_blocks,
        },
        "best_practices": {
            "checks": best_practice_checks,
            "issues": issues,
        },
        "recommendations": [
            "Use variables for all configurable values",
            "Add Cloud Monitoring alerts for critical resources",
            "Use modules for reusable infrastructure patterns",
        ] if not issues else issues,
    }

    return _wrap(result, "validate_terraform_syntax")


@tool
def list_available_resources(service: str) -> str:
    """
    List available Terraform resources for a specific GCP service.

    Args:
        service: GCP service name (compute, cloud_run, cloud_sql, memorystore, gcs, cloud_functions, lb)

    Returns:
        JSON string with available resources and their descriptions
    """
    resources_db = {
        "compute": [
            {"name": "google_compute_network", "description": "VPC network"},
            {"name": "google_compute_subnetwork", "description": "VPC subnetwork"},
            {"name": "google_compute_instance", "description": "Compute Engine VM instance"},
            {"name": "google_compute_firewall", "description": "Firewall rule"},
            {"name": "google_compute_router", "description": "Cloud Router"},
            {"name": "google_compute_router_nat", "description": "Cloud NAT"},
        ],
        "cloud_run": [
            {"name": "google_cloud_run_v2_service", "description": "Cloud Run service (v2)"},
            {"name": "google_cloud_run_v2_job", "description": "Cloud Run job (v2)"},
            {"name": "google_cloud_run_v2_service_iam_member", "description": "IAM binding for Cloud Run"},
        ],
        "cloud_sql": [
            {"name": "google_sql_database_instance", "description": "Cloud SQL instance"},
            {"name": "google_sql_database", "description": "Database within instance"},
            {"name": "google_sql_user", "description": "Database user"},
        ],
        "memorystore": [
            {"name": "google_redis_instance", "description": "Memorystore Redis instance"},
            {"name": "google_redis_cluster", "description": "Memorystore Redis cluster"},
        ],
        "gcs": [
            {"name": "google_storage_bucket", "description": "Cloud Storage bucket"},
            {"name": "google_storage_bucket_object", "description": "Object in a bucket"},
            {"name": "google_storage_bucket_iam_member", "description": "IAM binding for bucket"},
        ],
        "cloud_functions": [
            {"name": "google_cloudfunctions2_function", "description": "Cloud Functions (2nd gen)"},
            {"name": "google_cloudfunctions_function", "description": "Cloud Functions (1st gen)"},
        ],
        "lb": [
            {"name": "google_compute_global_forwarding_rule", "description": "Global forwarding rule"},
            {"name": "google_compute_backend_service", "description": "Backend service"},
            {"name": "google_compute_url_map", "description": "URL map for load balancing"},
            {"name": "google_compute_target_http_proxy", "description": "HTTP proxy"},
            {"name": "google_compute_health_check", "description": "Health check"},
        ],
    }

    service_lower = service.lower()
    resources = resources_db.get(service_lower, [])

    if not resources:
        result = {
            "service": service,
            "resources": [],
            "message": f"No resources found for service: {service}",
            "available_services": list(resources_db.keys()),
        }
    else:
        result = {
            "service": service,
            "resources": resources,
            "total": len(resources),
            "documentation": f"https://registry.terraform.io/providers/hashicorp/google/latest/docs",
        }

    return _wrap(result, "list_available_resources")


@tool
def generate_terraform_tests(module_name: str, module_type: str) -> str:
    """
    Generate test file for a Terraform module.

    Creates tests that verify:
    - Module validates without errors
    - Required resources are created
    - Security configurations are correct

    Args:
        module_name: Name of the module (e.g., "network")
        module_type: Type of module (network, cloud_run, cloud_sql, etc.)

    Returns:
        JSON string with generated test code
    """
    test_template = f'''# Test suite for {module_name} Terraform module
# Uses terraform validate and plan for verification

variable "project_id" {{
  default = "test-project-123"
}}

variable "region" {{
  default = "us-central1"
}}

variable "environment" {{
  default = "test"
}}

# Include the module under test
module "{module_type}_test" {{
  source = "../modules/{module_type}"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}}

# Verify outputs are defined
output "test_{module_type}_outputs" {{
  value = module.{module_type}_test
}}
'''

    result = {
        "module_name": module_name,
        "module_type": module_type,
        "test_code": test_template,
        "test_file_name": f"test_{module_type}.tf",
        "required_tools": [
            "terraform >= 1.0",
            "google provider ~> 5.0",
        ],
        "run_command": f"cd tests && terraform init && terraform validate && terraform plan",
    }

    return _wrap(result, "generate_terraform_tests")


ALL_TOOLS = [
    analyze_infrastructure_requirements,
    generate_terraform_module,
    validate_terraform_syntax,
    list_available_resources,
    generate_terraform_tests,
]
