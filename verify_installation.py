#!/usr/bin/env python3
"""
verify_installation.py
======================
Verify that Module 1 and Module 2 are correctly installed and importable.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_module1():
    """Verify Module 1 components."""
    print("Verifying Module 1 (GCP Infrastructure Agent)...")
    try:
        from module1.tools.gcp_tools import ALL_TOOLS
        from module1.config.models import get_vertex_model

        print(f"  ✓ Module 1 tools importable")
        print(f"  ✓ Module 1 has {len(ALL_TOOLS)} tools")
        print(f"  ✓ Module 1 configuration loaded (model: {get_vertex_model()})")
        return True
    except Exception as e:
        print(f"  ✗ Module 1 import failed: {e}")
        return False


def verify_module2():
    """Verify Module 2 components."""
    print("\nVerifying Module 2 (Repository Analysis Agent)...")
    try:
        from module2.agent import create_agent, analyze_repository
        from module2.config.models import get_chat_vertex_model
        from module2.tools.repo_tools import ALL_TOOLS
        from module2.workflows.analysis_graph import create_analysis_graph

        print(f"  ✓ Module 2 agent importable")
        print(f"  ✓ Module 2 has {len(ALL_TOOLS)} tools")
        print(f"  ✓ Module 2 configuration loaded")
        print(f"  ✓ Module 2 LangGraph workflow loaded")
        return True
    except Exception as e:
        print(f"  ✗ Module 2 import failed: {e}")
        return False


def verify_demos():
    """Verify demo scripts exist."""
    print("\nVerifying demo scripts...")
    demos = [
        "demos/module1_demo.py",
        "demos/module2_demo.py",
    ]

    all_exist = True
    for demo in demos:
        if Path(demo).exists():
            print(f"  ✓ {demo} exists")
        else:
            print(f"  ✗ {demo} missing")
            all_exist = False

    return all_exist


def verify_tests():
    """Verify test files exist."""
    print("\nVerifying test files...")
    tests = [
        "tests/test_tools.py",
        "tests/test_repo_tools.py",
    ]

    all_exist = True
    for test in tests:
        if Path(test).exists():
            print(f"  ✓ {test} exists")
        else:
            print(f"  ✗ {test} missing")
            all_exist = False

    return all_exist


def verify_documentation():
    """Verify documentation exists."""
    print("\nVerifying documentation...")
    docs = [
        "README.md",
        "GETTING_STARTED.md",
        "IMPLEMENTATION_SUMMARY.md",
        "module2/README.md",
    ]

    all_exist = True
    for doc in docs:
        if Path(doc).exists():
            print(f"  ✓ {doc} exists")
        else:
            print(f"  ✗ {doc} missing")
            all_exist = False

    return all_exist


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("AI Agent Learning Series - Installation Verification")
    print("=" * 60)

    results = {
        "Module 1": verify_module1(),
        "Module 2": verify_module2(),
        "Demos": verify_demos(),
        "Tests": verify_tests(),
        "Documentation": verify_documentation(),
    }

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{component:20s} {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n✓ All components verified successfully!")
        print("\nNext steps:")
        print("  1. Authenticate: gcloud auth application-default login")
        print("  2. Run Module 1 demo: AGENT_MOCK_GCP=true python demos/module1_demo.py")
        print("  3. Run Module 2 demo: AGENT_MOCK_REPO=true python demos/module2_demo.py")
        print("  4. See GETTING_STARTED.md for detailed instructions")
        return 0
    else:
        print("\n✗ Some components failed verification")
        print("Please check the errors above and ensure all files are present")
        return 1


if __name__ == "__main__":
    sys.exit(main())
