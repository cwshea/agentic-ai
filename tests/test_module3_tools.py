"""
tests/test_module3_tools.py
============================
Tests for Module 3 Terraform generation tools.
"""

import json
import os
import pytest

os.environ["AGENT_MOCK_REPO"] = "true"

from module3.tools.terraform_tools import (
    analyze_infrastructure_requirements,
    generate_terraform_module,
    validate_terraform_syntax,
    list_available_resources,
    generate_terraform_tests,
)


def test_analyze_infrastructure_requirements_mock():
    """Test infrastructure requirements analysis in mock mode."""
    requirements = json.dumps({
        "compute": "Cloud Run",
        "database": "Cloud SQL PostgreSQL",
    })

    result = analyze_infrastructure_requirements.invoke(requirements)
    data = json.loads(result)

    assert data["tool"] == "analyze_infrastructure_requirements"
    assert data["mock_mode"] is True
    assert "parsed_requirements" in data["data"]
    assert "recommended_modules" in data["data"]


def test_generate_terraform_module_network():
    """Test VPC network module generation."""
    parameters = json.dumps({"vpc_name": "main"})

    result = generate_terraform_module.invoke({"module_type": "network", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "network"
    assert data["data"]["syntax_valid"] is True
    assert "google_compute_network" in data["data"]["code"]
    assert "google_compute_subnetwork" in data["data"]["code"]


def test_generate_terraform_module_cloud_sql():
    """Test Cloud SQL module generation."""
    parameters = json.dumps({
        "database_version": "POSTGRES_15",
        "availability_type": "REGIONAL",
    })

    result = generate_terraform_module.invoke({"module_type": "cloud_sql", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "cloud_sql"
    assert data["data"]["syntax_valid"] is True
    assert "google_sql_database_instance" in data["data"]["code"]


def test_generate_terraform_module_cloud_run():
    """Test Cloud Run module generation."""
    parameters = json.dumps({
        "service_name": "api",
        "container_port": 8080,
    })

    result = generate_terraform_module.invoke({"module_type": "cloud_run", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "cloud_run"
    assert "google_cloud_run_v2_service" in data["data"]["code"]


def test_generate_terraform_module_memorystore():
    """Test Memorystore module generation."""
    parameters = json.dumps({
        "redis_version": "7_0",
        "memory_size_gb": 1,
    })

    result = generate_terraform_module.invoke({"module_type": "memorystore", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "memorystore"
    assert "google_redis_instance" in data["data"]["code"]


def test_generate_terraform_module_gcs():
    """Test Cloud Storage module generation."""
    parameters = json.dumps({"versioned": True})

    result = generate_terraform_module.invoke({"module_type": "gcs", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "gcs"
    assert "google_storage_bucket" in data["data"]["code"]


def test_generate_terraform_module_cloud_functions():
    """Test Cloud Functions module generation."""
    parameters = json.dumps({
        "runtime": "python312",
        "memory": 256,
    })

    result = generate_terraform_module.invoke({"module_type": "cloud_functions", "parameters": parameters})
    data = json.loads(result)

    assert data["data"]["module_type"] == "cloud_functions"
    assert "google_cloudfunctions2_function" in data["data"]["code"]


def test_generate_terraform_module_unknown_type():
    """Test handling of unknown module type."""
    result = generate_terraform_module.invoke({"module_type": "unknown_type", "parameters": "{}"})
    data = json.loads(result)

    assert "error" in data["data"]


def test_validate_terraform_syntax_valid():
    """Test validation of valid Terraform code."""
    valid_code = '''
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
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

resource "google_compute_network" "vpc" {
  name                    = "test-vpc"
  auto_create_subnetworks = false
}
'''

    result = validate_terraform_syntax.invoke(valid_code)
    data = json.loads(result)

    assert data["data"]["status"] == "PASS"
    assert data["data"]["syntax"]["valid"] is True


def test_validate_terraform_syntax_invalid():
    """Test validation of invalid Terraform code."""
    invalid_code = "resource broken { syntax here"

    result = validate_terraform_syntax.invoke(invalid_code)
    data = json.loads(result)

    assert data["data"]["status"] == "FAIL"
    assert data["data"]["syntax"]["valid"] is False


def test_list_available_resources_compute():
    """Test listing compute resources."""
    result = list_available_resources.invoke("compute")
    data = json.loads(result)

    assert data["data"]["service"] == "compute"
    assert len(data["data"]["resources"]) > 0
    assert any(r["name"] == "google_compute_network" for r in data["data"]["resources"])


def test_list_available_resources_cloud_run():
    """Test listing Cloud Run resources."""
    result = list_available_resources.invoke("cloud_run")
    data = json.loads(result)

    assert data["data"]["service"] == "cloud_run"
    assert any(r["name"] == "google_cloud_run_v2_service" for r in data["data"]["resources"])


def test_list_available_resources_unknown():
    """Test listing resources for unknown service."""
    result = list_available_resources.invoke("unknown_service")
    data = json.loads(result)

    assert len(data["data"]["resources"]) == 0
    assert "available_services" in data["data"]


def test_generate_terraform_tests():
    """Test Terraform test generation."""
    result = generate_terraform_tests.invoke({"module_name": "network", "module_type": "network"})
    data = json.loads(result)

    assert data["data"]["module_name"] == "network"
    assert data["data"]["module_type"] == "network"
    assert "terraform" in data["data"]["run_command"]


def test_all_tools_return_json():
    """Test that all tools return valid JSON."""
    tools = [
        (analyze_infrastructure_requirements, "{}"),
        (generate_terraform_module, {"module_type": "network", "parameters": "{}"}),
        (validate_terraform_syntax, 'resource "google_compute_network" "vpc" { name = "test" }'),
        (list_available_resources, "compute"),
        (generate_terraform_tests, {"module_name": "test", "module_type": "test"}),
    ]

    for tool_func, args in tools:
        result = tool_func.invoke(args)
        data = json.loads(result)
        assert "tool" in data
        assert "timestamp" in data
        assert "data" in data
