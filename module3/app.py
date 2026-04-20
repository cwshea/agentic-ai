"""
module3/app.py
==============
HTTP server for Module 3 Terraform Infrastructure Generation Agent.

Provides REST API endpoints for Terraform generation and validation.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from module3.agent import create_agent, generate_infrastructure, validate_terraform_code


PORT = int(os.getenv("MODULE3_PORT", "8082"))
HOST = os.getenv("MODULE3_HOST", "0.0.0.0")
VERBOSE = os.getenv("MODULE3_VERBOSE", "false").lower() == "true"


class Module3Handler(BaseHTTPRequestHandler):
    """HTTP request handler for Module 3 Terraform generation endpoints."""

    def _send_json_response(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _send_error_response(self, message: str, status: int = 400) -> None:
        self._send_json_response({"error": message}, status)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/ping":
            self._send_json_response({
                "status": "healthy",
                "service": "module3-terraform-agent",
                "version": "0.1.0",
            })
        else:
            self._send_error_response("Not found", 404)

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_error_response("Invalid JSON in request body")
                return

            if self.path == "/generate":
                self._handle_generate(data)
            elif self.path == "/validate":
                self._handle_validate(data)
            elif self.path == "/analyze":
                self._handle_analyze(data)
            else:
                self._send_error_response("Not found", 404)
        except Exception as e:
            self._send_error_response(f"Internal server error: {str(e)}", 500)

    def _handle_generate(self, data: dict[str, Any]) -> None:
        requirements = data.get("requirements")
        if not requirements:
            self._send_error_response("Missing 'requirements' in request body")
            return

        region = data.get("region", "us-central1")
        environment = data.get("environment", "dev")

        try:
            result = generate_infrastructure(
                requirements=requirements,
                region=region,
                environment=environment,
                verbose=VERBOSE,
            )
            self._send_json_response({
                "status": "success",
                "region": region,
                "environment": environment,
                "output": result["output"],
            })
        except Exception as e:
            self._send_error_response(f"Generation failed: {str(e)}", 500)

    def _handle_validate(self, data: dict[str, Any]) -> None:
        terraform_code = data.get("terraform_code")
        if not terraform_code:
            self._send_error_response("Missing 'terraform_code' in request body")
            return

        try:
            result = validate_terraform_code(terraform_code=terraform_code, verbose=VERBOSE)
            self._send_json_response({
                "status": "success",
                "validation_output": result["validation_output"],
            })
        except Exception as e:
            self._send_error_response(f"Validation failed: {str(e)}", 500)

    def _handle_analyze(self, data: dict[str, Any]) -> None:
        requirements = data.get("requirements")
        if not requirements:
            self._send_error_response("Missing 'requirements' in request body")
            return

        try:
            agent = create_agent(verbose=VERBOSE)
            if isinstance(requirements, dict):
                req_str = json.dumps(requirements, indent=2)
            else:
                req_str = str(requirements)

            query = f"""Analyze these infrastructure requirements and provide:
1. Parsed requirements (structured format)
2. Recommended Terraform modules
3. Any clarifying questions needed

Requirements:
{req_str}

Do NOT generate code yet, just analyze and provide recommendations.
"""
            result = agent.invoke({"messages": [("user", query)]})
            messages = result.get("messages", [])
            final_output = messages[-1].content if messages else ""

            self._send_json_response({"status": "success", "analysis": final_output})
        except Exception as e:
            self._send_error_response(f"Analysis failed: {str(e)}", 500)

    def log_message(self, format: str, *args: Any) -> None:
        if VERBOSE:
            print(f"[Module3] {format % args}")


def run_server(port: int = PORT, host: str = HOST) -> None:
    server = HTTPServer((host, port), Module3Handler)
    print(f"""
  Module 3: Terraform Infrastructure Generation Agent
  Server running on http://{host}:{port}

  Endpoints:
    GET  /ping              - Health check
    POST /analyze           - Analyze infrastructure requirements
    POST /generate          - Generate Terraform infrastructure code
    POST /validate          - Validate Terraform code

  Example:
    curl -X POST http://localhost:{port}/generate \\
      -H "Content-Type: application/json" \\
      -d '{{"requirements": {{"compute": "Cloud Run", "database": "Cloud SQL"}}, "region": "us-central1"}}'

  Press Ctrl+C to stop
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
