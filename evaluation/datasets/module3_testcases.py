"""
evaluation/datasets/module3_testcases.py
=========================================
Test cases for Module 3 Terraform Generation Agent evaluation.

Each test case includes:
- Input: Infrastructure requirements
- Expected output: Terraform code characteristics
- Evaluation criteria: How to score the generated code
"""

from __future__ import annotations

MODULE3_TEST_CASES = [
    # Simple web application patterns
    {
        "id": "m3-001",
        "name": "Simple Web App with Database",
        "category": "simple",
        "input": {
            "requirements": {
                "compute": "Cloud Run",
                "database": "Cloud SQL PostgreSQL",
                "networking": "VPC with Cloud Load Balancing",
            },
            "region": "us-central1",
            "environment": "dev",
        },
        "expected_output": {
            "modules": ["network", "cloud_sql", "cloud_run"],
            "resources": ["google_compute_network", "google_sql_database_instance", "google_cloud_run_v2_service", "google_compute_global_forwarding_rule"],
            "security": ["firewall", "encryption", "high_availability"],
        },
        "evaluation_criteria": {
            "syntax_correctness": "Valid Terraform HCL syntax",
            "completeness": "All required resources (VPC, Cloud SQL, Cloud Run, LB) are included",
            "best_practices": "HA deployment, encryption, proper firewall rules",
            "security": "Service accounts, firewall rules, encryption at rest and in transit",
        },
    },
    {
        "id": "m3-002",
        "name": "Serverless API with Firestore",
        "category": "serverless",
        "input": {
            "requirements": {
                "compute": "Cloud Functions",
                "database": "Firestore",
                "api": "API Gateway",
            },
            "region": "us-west1",
            "environment": "prod",
        },
        "expected_output": {
            "modules": ["cloud_functions", "firestore", "api_gateway"],
            "resources": ["google_cloudfunctions2_function", "google_firestore_database", "google_api_gateway_api"],
            "security": ["service_account", "encryption"],
        },
        "evaluation_criteria": {
            "syntax_correctness": "Valid Terraform code with proper provider config",
            "completeness": "Cloud Functions, Firestore, API Gateway all configured",
            "best_practices": "Point-in-time recovery, encryption, proper IAM",
            "security": "Least privilege service accounts, encryption, API authentication",
        },
    },

    # Microservices patterns
    {
        "id": "m3-003",
        "name": "Microservices with Service Mesh",
        "category": "microservices",
        "input": {
            "requirements": {
                "compute": "Cloud Run",
                "services": ["api", "worker", "scheduler"],
                "database": "Cloud SQL PostgreSQL",
                "cache": "Memorystore Redis",
                "queue": "Cloud Pub/Sub",
            },
            "region": "us-central1",
            "environment": "prod",
        },
        "expected_output": {
            "modules": ["network", "cloud_sql", "memorystore", "cloud_run"],
            "resources": ["google_compute_network", "google_sql_database_instance", "google_redis_instance", "google_cloud_run_v2_service", "google_pubsub_topic"],
            "multi_service": True,
        },
        "evaluation_criteria": {
            "syntax_correctness": "Valid Terraform code for all modules",
            "completeness": "All services, database, cache, and queue configured",
            "best_practices": "Service discovery, auto-scaling, Cloud Monitoring",
            "security": "Network isolation, encryption, service accounts per service",
        },
    },

    # Data pipeline patterns
    {
        "id": "m3-004",
        "name": "Data Processing Pipeline",
        "category": "data",
        "input": {
            "requirements": {
                "ingestion": "Cloud Pub/Sub",
                "processing": "Cloud Functions",
                "storage": "Cloud Storage",
                "analytics": "BigQuery",
            },
            "region": "us-central1",
            "environment": "prod",
        },
        "expected_output": {
            "modules": ["pubsub", "cloud_functions", "gcs", "bigquery"],
            "resources": ["google_pubsub_topic", "google_cloudfunctions2_function", "google_storage_bucket", "google_bigquery_dataset"],
            "data_flow": True,
        },
        "evaluation_criteria": {
            "syntax_correctness": "Valid Terraform code with data pipeline resources",
            "completeness": "Complete data flow from ingestion to analytics",
            "best_practices": "Data partitioning, lifecycle policies, Cloud Monitoring",
            "security": "Encryption at rest and in transit, IAM policies",
        },
    },

    # High availability patterns
    {
        "id": "m3-005",
        "name": "High Availability Web Application",
        "category": "ha",
        "input": {
            "requirements": {
                "compute": "Cloud Run",
                "database": "Cloud SQL PostgreSQL (HA)",
                "cache": "Memorystore Redis (HA)",
                "cdn": "Cloud CDN",
                "availability": "multi-region",
            },
            "region": "us-central1",
            "environment": "prod",
        },
        "expected_output": {
            "modules": ["network", "cloud_sql", "memorystore", "cloud_run", "cloud_cdn"],
            "resources": ["google_sql_database_instance", "google_redis_instance", "google_cloud_run_v2_service", "google_compute_backend_service"],
            "ha_features": ["regional_availability", "read_replicas", "automatic_failover"],
        },
        "evaluation_criteria": {
            "syntax_correctness": "Valid Terraform code for HA configuration",
            "completeness": "All HA components configured correctly",
            "best_practices": "Regional HA, read replicas, automatic failover, health checks",
            "security": "Encryption, network isolation, Cloud Armor protection",
        },
    },
]

# Evaluation criteria descriptions for Module 3
MODULE3_EVALUATION_CRITERIA = {
    "syntax_correctness": "Is the generated Terraform code syntactically valid HCL that can be validated without errors?",
    "completeness": "Are all required GCP resources included in the generated modules? Are there any missing components?",
    "best_practices": "Does the code follow GCP and Terraform best practices such as HA deployments, proper labeling, monitoring, and resource organization?",
    "security": "Are proper security configurations in place including encryption, service accounts, firewall rules, and network isolation?",
}
