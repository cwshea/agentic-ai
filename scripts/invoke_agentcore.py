#!/usr/bin/env python3
"""
scripts/invoke_agentcore.py
============================
Invoke the Infrastructure Agent deployed on Cloud Run.

Use this after deploying the agent to Cloud Run with `gcloud run deploy`.

USAGE
-----
  # Set your Cloud Run service URL
  export AGENT_URL="https://gcp-infra-agent-xxxxx-uc.a.run.app"

  # Single prompt
  python scripts/invoke_agentcore.py --prompt "Health check us-central1"

  # Interactive REPL
  python scripts/invoke_agentcore.py --repl
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests


def invoke(agent_url: str, prompt: str) -> str:
    """Send a prompt to the deployed Cloud Run agent and return the response."""
    url = f"{agent_url.rstrip('/')}/invocations"

    response = requests.post(
        url,
        json={"prompt": prompt},
        headers={"Content-Type": "application/json"},
        timeout=600,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("result", json.dumps(data))


def main() -> None:
    parser = argparse.ArgumentParser(description="Invoke Cloud Run-deployed Infrastructure Agent")
    parser.add_argument("--url", default=os.getenv("AGENT_URL"), help="Cloud Run service URL")
    parser.add_argument("--prompt", "-p", help="Single prompt to send")
    parser.add_argument("--repl", action="store_true", help="Interactive mode")
    args = parser.parse_args()

    if not args.url:
        print("Error: provide --url or set AGENT_URL environment variable.")
        print("The URL is printed during `gcloud run deploy`.")
        sys.exit(1)

    if args.prompt:
        print(f"\nPrompt: {args.prompt}")
        print(f"\nResponse:\n{invoke(args.url, args.prompt)}\n")

    elif args.repl:
        print(f"\nInfrastructure Agent (Cloud Run)")
        print(f"URL: {args.url}")
        print(f"Type 'quit' to exit.\n")
        while True:
            try:
                prompt = input("You › ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if prompt.lower() in ("quit", "exit", "q"):
                break
            if not prompt:
                continue
            print(f"\nAgent › {invoke(args.url, prompt)}\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
