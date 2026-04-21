"""
app.py
======
HTTP server entrypoint for the GCP Infrastructure Agent.

This file wraps the ADK agent in a simple HTTP server, converting it
into a deployable service with:
  - POST /invocations  : invoke the agent
  - GET  /ping         : health check

Deploy to Cloud Run for production use.

MODULE 1 CONCEPT: The Deployment-Logic Separation
---------------------------------------------------
Notice how little code is here. The agent logic (agent.py) is completely
unchanged when deploying to Cloud Run. This is the same abstraction arc
the Module 1 slides describe: your agent IS the application; Cloud Run
is the managed runtime platform.

DEPLOYMENT STEPS
-----------------
  # 1. Test locally (serves on http://localhost:8080)
  python module1/app.py

  # 2. Test the local server
  curl -X POST http://localhost:8080/invocations \\
    -H "Content-Type: application/json" \\
    -d '{"prompt": "Give me a health summary of us-central1"}'

  # 3. Deploy to Cloud Run
  gcloud run deploy gcp-infra-agent \\
    --source . \\
    --region us-central1 \\
    --allow-unauthenticated

MOCK MODE
----------
Set AGENT_MOCK_GCP=true to run without real GCP credentials.
The agent responds with realistic simulated data — good for demos.

  AGENT_MOCK_GCP=true python module1/app.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module1.agent import create_agent


# ---------------------------------------------------------------------------
# Shared agent instance (created once at startup, reused across requests)
# ---------------------------------------------------------------------------

_model_garden_endpoint = os.getenv("MODEL_GARDEN_ENDPOINT")

print("\n  Initialising GCP Infrastructure Agent...")
_agent = create_agent(
    model_garden_endpoint=_model_garden_endpoint if _model_garden_endpoint else None,
    verbose=False,
)
print("  Agent ready.\n")


# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

def _handle(payload: dict) -> dict:
    """
    Process an incoming agent request.

    Expected payload
    ----------------
    {
      "prompt"  : str   — required: the user's instruction
      "region"  : str   — optional: override GCP region for this request
      "verbose" : bool  — optional: print loop steps to console (local dev)
    }
    """
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return {"error": "Missing required field: 'prompt'"}

    region = payload.get("region")
    if region:
        os.environ["GCP_REGION"] = region

    if payload.get("verbose"):
        local_agent = create_agent(
            model_garden_endpoint=_model_garden_endpoint if _model_garden_endpoint else None,
            verbose=True,
        )
        response = local_agent(prompt)
    else:
        response = _agent(prompt)

    return {
        "result": str(response),
        "region": os.getenv("GCP_REGION", "us-central1"),
        "mock_mode": os.getenv("AGENT_MOCK_GCP", "false").lower() == "true",
        "model": "model-garden" if _model_garden_endpoint else "gemini-2.5-flash",
    }


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

def _run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """HTTP server that provides the /invocations interface."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: object) -> None:
            pass

        def do_GET(self) -> None:
            if self.path == "/ping":
                self._respond(200, {"status": "ok"})
            else:
                self._respond(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/invocations":
                self._respond(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length))
            except json.JSONDecodeError:
                self._respond(400, {"error": "invalid JSON"})
                return
            self._respond(200, _handle(body))

        def _respond(self, code: int, data: dict) -> None:
            payload = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    mock = os.getenv("AGENT_MOCK_GCP", "false").lower() == "true"
    print(f"  🚀  Infrastructure Agent HTTP server")
    print(f"      http://{host}:{port}/invocations  (POST)")
    print(f"      http://{host}:{port}/ping         (GET)")
    print(f"      Mock mode : {'ON — no GCP credentials needed' if mock else 'OFF — using live GCP'}")
    print(f"\n  Example:")
    print(f"    curl -X POST http://localhost:{port}/invocations \\")
    print(f"      -H 'Content-Type: application/json' \\")
    print(f"      -d '{{\"prompt\": \"Give me a health summary of us-central1\"}}'")
    print(f"\n  Ctrl-C to stop.\n")

    server = HTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
    finally:
        _agent.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _run_server()
