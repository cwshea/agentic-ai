"""
module3.tools
=============
Terraform generation and validation tools for Module 3.
"""

from module3.tools.terraform_tools import (
    ALL_TOOLS,
    analyze_infrastructure_requirements,
    generate_terraform_module,
    validate_terraform_syntax,
    list_available_resources,
    generate_terraform_tests,
)

__all__ = [
    "ALL_TOOLS",
    "analyze_infrastructure_requirements",
    "generate_terraform_module",
    "validate_terraform_syntax",
    "list_available_resources",
    "generate_terraform_tests",
]
