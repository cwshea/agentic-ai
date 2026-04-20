"""
module3/templates/terraform_modules.py
=======================================
Reusable Terraform module templates for common GCP infrastructure.

These templates follow GCP best practices:
- Regional deployments for high availability
- Encryption at rest and in transit
- Least privilege IAM (service accounts)
- Firewall rules with minimal access
- Cloud Monitoring and Logging
"""

from __future__ import annotations

from typing import Any


TERRAFORM_MODULES = {
    "network": '''terraform {{
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
  description = "GCP region"
  type        = string
  default     = "us-central1"
}}

resource "google_compute_network" "vpc" {{
  name                    = "{vpc_name}-vpc"
  auto_create_subnetworks = false
}}

resource "google_compute_subnetwork" "public" {{
  name          = "{vpc_name}-public"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}}

resource "google_compute_subnetwork" "private" {{
  name          = "{vpc_name}-private"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}}

resource "google_compute_router" "router" {{
  name    = "{vpc_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}}

resource "google_compute_router_nat" "nat" {{
  name                               = "{vpc_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}}

output "vpc_id" {{
  value = google_compute_network.vpc.id
}}

output "public_subnet_id" {{
  value = google_compute_subnetwork.public.id
}}

output "private_subnet_id" {{
  value = google_compute_subnetwork.private.id
}}
''',
    "cloud_run": '''resource "google_cloud_run_v2_service" "{service_name}" {{
  name     = "{service_name}"
  location = var.region

  template {{
    containers {{
      image = "{image}"

      ports {{
        container_port = {container_port}
      }}

      resources {{
        limits = {{
          cpu    = "{cpu}"
          memory = "{memory}"
        }}
      }}

      env {{
        name  = "ENVIRONMENT"
        value = var.environment
      }}
    }}

    scaling {{
      min_instance_count = {min_instances}
      max_instance_count = {max_instances}
    }}

    vpc_access {{
      network_interfaces {{
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.private.id
      }}
    }}
  }}

  traffic {{
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }}
}}

resource "google_cloud_run_v2_service_iam_member" "invoker" {{
  name     = google_cloud_run_v2_service.{service_name}.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}}

output "{service_name}_url" {{
  value = google_cloud_run_v2_service.{service_name}.uri
}}
''',
    "cloud_sql": '''resource "google_sql_database_instance" "{db_name}" {{
  name             = "{db_name}"
  database_version = "{database_version}"
  region           = var.region

  settings {{
    tier              = "{tier}"
    availability_type = "{availability_type}"
    disk_size         = {disk_size}

    backup_configuration {{
      enabled                        = true
      binary_log_enabled             = {binary_log}
      point_in_time_recovery_enabled = true
      backup_retention_settings {{
        retained_backups = {backup_retention}
      }}
    }}

    ip_configuration {{
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }}

    database_flags {{
      name  = "log_checkpoints"
      value = "on"
    }}
  }}

  deletion_protection = {deletion_protection}
}}

resource "google_sql_database" "{db_name}_db" {{
  name     = "{db_name}"
  instance = google_sql_database_instance.{db_name}.name
}}

resource "google_sql_user" "{db_name}_user" {{
  name     = "{db_name}-user"
  instance = google_sql_database_instance.{db_name}.name
  password = var.db_password
}}

output "{db_name}_connection_name" {{
  value = google_sql_database_instance.{db_name}.connection_name
}}
''',
    "memorystore": '''resource "google_redis_instance" "{cache_name}" {{
  name           = "{cache_name}"
  tier           = "{tier}"
  memory_size_gb = {memory_size_gb}
  region         = var.region

  redis_version = "REDIS_{redis_version}"

  authorized_network = google_compute_network.vpc.id

  transit_encryption_mode = "SERVER_AUTHENTICATION"

  replica_count       = {replica_count}
  read_replicas_mode  = "{read_replicas_mode}"

  persistence_config {{
    persistence_mode    = "RDB"
    rdb_snapshot_period = "TWELVE_HOURS"
  }}
}}

output "{cache_name}_host" {{
  value = google_redis_instance.{cache_name}.host
}}

output "{cache_name}_port" {{
  value = google_redis_instance.{cache_name}.port
}}
''',
    "gcs": '''resource "google_storage_bucket" "{bucket_name}" {{
  name     = "{bucket_name}-${{var.project_id}}"
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {{
    enabled = {versioned}
  }}

  encryption {{
    default_kms_key_name = null  # Uses Google-managed encryption
  }}

  lifecycle_rule {{
    condition {{
      age = 90
    }}
    action {{
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }}
  }}
}}

output "{bucket_name}_url" {{
  value = google_storage_bucket.{bucket_name}.url
}}
''',
    "cloud_functions": '''resource "google_cloudfunctions2_function" "{function_name}" {{
  name     = "{function_name}"
  location = var.region

  build_config {{
    runtime     = "{runtime}"
    entry_point = "{entry_point}"
    source {{
      storage_source {{
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_zip.name
      }}
    }}
  }}

  service_config {{
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "{memory}Mi"
    timeout_seconds    = {timeout}

    environment_variables = {{
      ENVIRONMENT = var.environment
    }}

    vpc_connector                 = google_vpc_access_connector.connector.id
    vpc_connector_egress_settings = "PRIVATE_RANGES_ONLY"

    service_account_email = google_service_account.function_sa.email
  }}
}}

resource "google_service_account" "function_sa" {{
  account_id   = "{function_name}-sa"
  display_name = "Service account for {function_name}"
}}

output "{function_name}_uri" {{
  value = google_cloudfunctions2_function.{function_name}.service_config[0].uri
}}
''',
}


def generate_network_module(
    vpc_name: str = "main",
) -> str:
    """Generate a VPC network module."""
    return TERRAFORM_MODULES["network"].format(vpc_name=vpc_name)


def generate_cloud_run_module(
    service_name: str = "app",
    image: str = "gcr.io/project/app:latest",
    container_port: int = 8080,
    cpu: str = "1",
    memory: str = "512Mi",
    min_instances: int = 1,
    max_instances: int = 10,
) -> str:
    """Generate a Cloud Run service module."""
    return TERRAFORM_MODULES["cloud_run"].format(
        service_name=service_name,
        image=image,
        container_port=container_port,
        cpu=cpu,
        memory=memory,
        min_instances=min_instances,
        max_instances=max_instances,
    )


def generate_cloud_sql_module(
    db_name: str = "app-db",
    database_version: str = "POSTGRES_15",
    tier: str = "db-custom-2-8192",
    availability_type: str = "REGIONAL",
    disk_size: int = 20,
    backup_retention: int = 7,
    deletion_protection: bool = True,
    binary_log: str = "false",
) -> str:
    """Generate a Cloud SQL database module."""
    return TERRAFORM_MODULES["cloud_sql"].format(
        db_name=db_name.replace("-", "_"),
        database_version=database_version,
        tier=tier,
        availability_type=availability_type,
        disk_size=disk_size,
        backup_retention=backup_retention,
        deletion_protection=str(deletion_protection).lower(),
        binary_log=binary_log,
    )


def generate_memorystore_module(
    cache_name: str = "redis-cache",
    tier: str = "STANDARD_HA",
    memory_size_gb: int = 1,
    redis_version: str = "7_0",
    replica_count: int = 1,
    read_replicas_mode: str = "READ_REPLICAS_ENABLED",
) -> str:
    """Generate a Memorystore Redis module."""
    return TERRAFORM_MODULES["memorystore"].format(
        cache_name=cache_name.replace("-", "_"),
        tier=tier,
        memory_size_gb=memory_size_gb,
        redis_version=redis_version,
        replica_count=replica_count,
        read_replicas_mode=read_replicas_mode,
    )


def generate_gcs_module(
    bucket_name: str = "app-bucket",
    versioned: bool = True,
) -> str:
    """Generate a Cloud Storage bucket module."""
    return TERRAFORM_MODULES["gcs"].format(
        bucket_name=bucket_name.replace("-", "_"),
        versioned=str(versioned).lower(),
    )


def generate_cloud_functions_module(
    function_name: str = "my-function",
    runtime: str = "python312",
    entry_point: str = "main",
    memory: int = 256,
    timeout: int = 60,
) -> str:
    """Generate a Cloud Functions module."""
    return TERRAFORM_MODULES["cloud_functions"].format(
        function_name=function_name.replace("-", "_"),
        runtime=runtime,
        entry_point=entry_point,
        memory=memory,
        timeout=timeout,
    )
