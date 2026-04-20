"""
tests/test_repo_tools.py
========================
Unit tests for Module 2 repository analysis tools.

Tests all five tools in both mock and real modes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_nodejs_repo():
    """Path to sample Node.js repository fixture."""
    return str(Path(__file__).parent / "fixtures" / "sample_repos" / "nodejs-app")


@pytest.fixture
def sample_python_repo():
    """Path to sample Python repository fixture."""
    return str(Path(__file__).parent / "fixtures" / "sample_repos" / "python-app")


@pytest.fixture
def enable_mock_mode():
    """Enable mock mode for tests."""
    original = os.environ.get("AGENT_MOCK_REPO")
    os.environ["AGENT_MOCK_REPO"] = "true"
    yield
    if original is None:
        os.environ.pop("AGENT_MOCK_REPO", None)
    else:
        os.environ["AGENT_MOCK_REPO"] = original


# ---------------------------------------------------------------------------
# Test scan_repository_structure
# ---------------------------------------------------------------------------

def test_scan_repository_structure_mock(enable_mock_mode):
    """Test repository scanning in mock mode."""
    from module2.tools.repo_tools import scan_repository_structure

    result = scan_repository_structure.invoke("/mock/repo/path")
    data = json.loads(result)

    assert data["tool"] == "scan_repository_structure"
    assert data["mock_mode"] is True
    assert "data" in data
    assert "files" in data["data"]
    assert "directories" in data["data"]
    assert len(data["data"]["files"]) > 0


def test_scan_repository_structure_error(monkeypatch):
    """Test scanning non-existent repository (non-mock mode)."""
    monkeypatch.delenv("AGENT_MOCK_REPO", raising=False)
    import importlib
    import module2.tools.repo_tools as rt
    monkeypatch.setattr(rt, "_MOCK", False)

    result = rt.scan_repository_structure.invoke("/nonexistent/path")
    data = json.loads(result)

    assert "error" in data["data"]


# ---------------------------------------------------------------------------
# Test read_file_content
# ---------------------------------------------------------------------------

def test_read_file_content_mock(enable_mock_mode):
    """Test reading file content in mock mode."""
    from module2.tools.repo_tools import read_file_content

    result = read_file_content.invoke({"repo_path": "/mock/repo", "file_path": "services/api/package.json"})
    data = json.loads(result)

    assert data["tool"] == "read_file_content"
    assert data["mock_mode"] is True
    assert "content" in data["data"]
    assert "express" in data["data"]["content"]


def test_read_file_content_not_found(enable_mock_mode):
    """Test reading non-existent file in mock mode."""
    from module2.tools.repo_tools import read_file_content

    result = read_file_content.invoke({"repo_path": "/mock/repo", "file_path": "nonexistent.txt"})
    data = json.loads(result)

    assert "error" in data["data"]


# ---------------------------------------------------------------------------
# Test detect_applications
# ---------------------------------------------------------------------------

def test_detect_applications_mock(enable_mock_mode):
    """Test application detection in mock mode."""
    from module2.tools.repo_tools import detect_applications, scan_repository_structure

    scan_result = scan_repository_structure.invoke("/mock/repo")

    result = detect_applications.invoke({"repo_path": "/mock/repo", "file_tree": scan_result})
    data = json.loads(result)

    assert data["tool"] == "detect_applications"
    assert data["mock_mode"] is True
    assert "applications" in data["data"]
    assert data["data"]["total_applications"] == 2
    assert any(app["name"] == "api-service" for app in data["data"]["applications"])


# ---------------------------------------------------------------------------
# Test analyze_dependencies
# ---------------------------------------------------------------------------

def test_analyze_dependencies_nodejs_mock(enable_mock_mode):
    """Test dependency analysis for Node.js in mock mode."""
    from module2.tools.repo_tools import analyze_dependencies

    result = analyze_dependencies.invoke({"repo_path": "/mock/repo", "app_path": "services/api", "dependency_file": "package.json"})
    data = json.loads(result)

    assert data["tool"] == "analyze_dependencies"
    assert "language" in data["data"]
    assert data["data"]["language"] == "Node.js"
    assert data["data"]["framework"] == "Express"
    assert "pg" in data["data"]["dependencies"]
    assert "redis" in data["data"]["dependencies"]


def test_analyze_dependencies_python_mock(enable_mock_mode):
    """Test dependency analysis for Python in mock mode."""
    from module2.tools.repo_tools import analyze_dependencies

    result = analyze_dependencies.invoke({"repo_path": "/mock/repo", "app_path": "services/worker", "dependency_file": "requirements.txt"})
    data = json.loads(result)

    assert data["tool"] == "analyze_dependencies"
    assert "language" in data["data"]
    assert data["data"]["language"] == "Python"
    assert data["data"]["framework"] == "FastAPI"
    assert "celery" in data["data"]["dependencies"]


# ---------------------------------------------------------------------------
# Test map_gcp_services
# ---------------------------------------------------------------------------

def test_map_gcp_services_mock(enable_mock_mode):
    """Test GCP service mapping in mock mode."""
    from module2.tools.repo_tools import analyze_dependencies, map_gcp_services

    deps_result = analyze_dependencies.invoke({"repo_path": "/mock/repo", "app_path": "services/api", "dependency_file": "package.json"})

    result = map_gcp_services.invoke(deps_result)
    data = json.loads(result)

    assert data["tool"] == "map_gcp_services"
    assert "gcp_services" in data["data"]
    assert "database" in data["data"]["gcp_services"]
    assert "cache" in data["data"]["gcp_services"]
    assert "storage" in data["data"]["gcp_services"]
    assert "compute" in data["data"]["gcp_services"]

    db_services = data["data"]["gcp_services"]["database"]
    assert any(s["service"] == "Cloud SQL" and s["engine"] == "PostgreSQL" for s in db_services)

    cache_services = data["data"]["gcp_services"]["cache"]
    assert any(s["service"] == "Memorystore" and s["engine"] == "Redis" for s in cache_services)


def test_map_gcp_services_summary(enable_mock_mode):
    """Test GCP service mapping summary."""
    from module2.tools.repo_tools import analyze_dependencies, map_gcp_services

    deps_result = analyze_dependencies.invoke({"repo_path": "/mock/repo", "app_path": "services/api", "dependency_file": "package.json"})
    result = map_gcp_services.invoke(deps_result)
    data = json.loads(result)

    assert "summary" in data["data"]
    summary = data["data"]["summary"]
    assert "databases" in summary
    assert "caching" in summary
    assert "storage" in summary
    assert "compute" in summary
    assert "Cloud SQL" in summary["databases"]
    assert "Memorystore" in summary["caching"]


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

def test_full_analysis_workflow_mock(enable_mock_mode):
    """Test complete analysis workflow in mock mode."""
    from module2.tools.repo_tools import (
        analyze_dependencies,
        detect_applications,
        map_gcp_services,
        scan_repository_structure,
    )

    repo_path = "/mock/repo"

    scan_result = scan_repository_structure.invoke(repo_path)
    scan_data = json.loads(scan_result)
    assert "files" in scan_data["data"]

    detect_result = detect_applications.invoke({"repo_path": repo_path, "file_tree": scan_result})
    detect_data = json.loads(detect_result)
    assert detect_data["data"]["total_applications"] > 0

    apps = detect_data["data"]["applications"]
    first_app = apps[0]

    dep_file = "package.json" if "package.json" in first_app["indicators"] else "requirements.txt"

    deps_result = analyze_dependencies.invoke({"repo_path": repo_path, "app_path": first_app["path"], "dependency_file": dep_file})
    deps_data = json.loads(deps_result)
    assert "dependencies" in deps_data["data"]

    gcp_result = map_gcp_services.invoke(deps_result)
    gcp_data = json.loads(gcp_result)
    assert "gcp_services" in gcp_data["data"]
    assert len(gcp_data["data"]["gcp_services"]) > 0


# ---------------------------------------------------------------------------
# Dependency Mapping Tests
# ---------------------------------------------------------------------------

def test_dependency_mapping_coverage():
    """Test that common dependencies are mapped correctly."""
    from module2.tools.repo_tools import DEPENDENCY_TO_GCP_SERVICE

    assert "pg" in DEPENDENCY_TO_GCP_SERVICE
    assert DEPENDENCY_TO_GCP_SERVICE["pg"]["service"] == "Cloud SQL"
    assert DEPENDENCY_TO_GCP_SERVICE["pg"]["engine"] == "PostgreSQL"

    assert "mysql" in DEPENDENCY_TO_GCP_SERVICE
    assert DEPENDENCY_TO_GCP_SERVICE["mysql"]["service"] == "Cloud SQL"

    assert "mongodb" in DEPENDENCY_TO_GCP_SERVICE
    assert DEPENDENCY_TO_GCP_SERVICE["mongodb"]["service"] == "Firestore"

    assert "redis" in DEPENDENCY_TO_GCP_SERVICE
    assert DEPENDENCY_TO_GCP_SERVICE["redis"]["service"] == "Memorystore"

    assert "google-cloud-storage" in DEPENDENCY_TO_GCP_SERVICE
    assert DEPENDENCY_TO_GCP_SERVICE["google-cloud-storage"]["service"] == "Cloud Storage"

    assert "express" in DEPENDENCY_TO_GCP_SERVICE
    assert "fastapi" in DEPENDENCY_TO_GCP_SERVICE
    assert "flask" in DEPENDENCY_TO_GCP_SERVICE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
