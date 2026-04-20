"""
module3.templates
=================
Terraform module templates for common GCP infrastructure.
"""

from module3.templates.terraform_modules import (
    TERRAFORM_MODULES,
    generate_network_module,
    generate_cloud_run_module,
    generate_cloud_sql_module,
    generate_memorystore_module,
    generate_gcs_module,
    generate_cloud_functions_module,
)

__all__ = [
    "TERRAFORM_MODULES",
    "generate_network_module",
    "generate_cloud_run_module",
    "generate_cloud_sql_module",
    "generate_memorystore_module",
    "generate_gcs_module",
    "generate_cloud_functions_module",
]
