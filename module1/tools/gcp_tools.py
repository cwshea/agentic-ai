"""
tools/gcp_tools.py
==================
Module 1 tool set for the GCP Infrastructure Agent.

DESIGN PRINCIPLES FOR MODULE 1
--------------------------------
All tools in this module are READ-ONLY. No infrastructure is created,
modified, or destroyed. This is intentional and reflects the Phase 1
(Assist) adoption pattern from the slides:

    Phase 1 — Assist  : Agent observes and recommends. Human acts.  <- we are here
    Phase 2 — Automate: Agent acts within guardrails.
    Phase 3 — Orchestrate: Full autonomous workflows.

The only "action" available is request_human_review, which creates a
structured escalation record for a human engineer to act on. This is the
Human-in-the-Loop pattern shown in the Architecture section of Module 1.

MOCK MODE
---------
Set AGENT_MOCK_GCP=true to run without real GCP credentials.
All tools return realistic simulated data so the agent behaves identically
to a real GCP environment — perfect for live demos and workshops.

WHAT EACH TOOL DEMONSTRATES (tie-back to slide content)
--------------------------------------------------------
  list_gcp_resources    -> Tools connect the agent to external systems
  describe_resource     -> Grounding: agent gets current state, not training knowledge
  check_resource_health -> Observation: synthesized health assessment
  get_environment_summary -> Multi-source data aggregation
  request_human_review  -> Human-in-the-loop pattern (explicit escalation path)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MOCK = os.getenv("AGENT_MOCK_GCP", "false").lower() == "true"


def _project() -> str:
    return os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT") or "workshop-project"


def _region() -> str:
    return os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"


def _client(service: str, region: str | None = None) -> Any:
    """Create a GCP service client. Each service uses its own client library."""
    try:
        if service == "run":
            from google.cloud import run_v2
            return run_v2.ServicesClient()
        elif service == "compute":
            from google.cloud import compute_v1
            return compute_v1.InstancesClient()
        elif service == "sqladmin":
            from googleapiclient.discovery import build
            return build("sqladmin", "v1beta4")
        elif service == "functions":
            from google.cloud import functions_v2
            return functions_v2.FunctionServiceClient()
        else:
            raise ValueError(f"Unknown service: {service}")
    except Exception as exc:
        if "credentials" in str(exc).lower() or "auth" in str(exc).lower():
            raise RuntimeError(
                "GCP credentials not found.\n"
                "Configure with: gcloud auth application-default login\n"
                "Or set AGENT_MOCK_GCP=true for demo mode."
            ) from exc
        raise


def _wrap(data: Any, tool_name: str) -> str:
    """
    Wrap tool output in a consistent JSON envelope.

    The agent reads tool output as text in its context window.
    Consistent structure + ISO timestamps help the model parse
    and cite results accurately.
    """
    return json.dumps(
        {
            "tool": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "region": _region(),
            "project": _project(),
            "mock_mode": _MOCK,
            "data": data,
        },
        indent=2,
        default=str,
    )


# ---------------------------------------------------------------------------
# Realistic mock data
# Mirrors what you'd see in a real GCP project running microservices.
# ---------------------------------------------------------------------------

_MOCK_CLOUD_RUN = {
    "us-central1": [
        {
            "name": "api-gateway-svc",
            "region": "us-central1",
            "status": "ACTIVE",
            "instances": 3,
            "min_instances": 3,
            "revision": "api-gateway-svc-00042",
            "platform": "managed",
        },
        {
            "name": "auth-service",
            "region": "us-central1",
            "status": "ACTIVE",
            "instances": 2,
            "min_instances": 2,
            "revision": "auth-service-00015",
            "platform": "managed",
        },
        {
            "name": "inventory-svc",
            "region": "us-central1",
            "status": "ACTIVE",
            "instances": 5,
            "min_instances": 5,
            "revision": "inventory-svc-00008",
            "platform": "managed",
        },
        {
            "name": "notification-svc",
            "region": "us-central1",
            "status": "ACTIVE",
            "instances": 1,
            "min_instances": 2,
            "revision": "notification-svc-00003",
            "platform": "managed",
            "note": "Running below minimum instances — possible container crash",
        },
    ],
    "us-west1": [
        {
            "name": "api-gateway-svc",
            "region": "us-west1",
            "status": "ACTIVE",
            "instances": 2,
            "min_instances": 2,
            "revision": "api-gateway-svc-00041",
            "platform": "managed",
        },
    ],
}

_MOCK_GCE = {
    "us-central1": [
        {"id": "1234567890001", "name": "gke-node-01", "machine_type": "e2-standard-4", "status": "RUNNING", "zone": "us-central1-a"},
        {"id": "1234567890002", "name": "gke-node-02", "machine_type": "e2-standard-4", "status": "RUNNING", "zone": "us-central1-b"},
        {"id": "1234567890003", "name": "bastion-host", "machine_type": "e2-medium",     "status": "RUNNING", "zone": "us-central1-a"},
        {"id": "1234567890004", "name": "dev-sandbox",  "machine_type": "e2-micro",      "status": "TERMINATED", "zone": "us-central1-c"},
    ],
}

_MOCK_CLOUD_SQL = {
    "us-central1": [
        {
            "name": "prod-postgres-01",
            "engine": "POSTGRES_15",
            "status": "RUNNABLE",
            "tier": "db-custom-4-16384",
            "high_availability": True,
            "storage_gb": 500,
            "region": "us-central1",
        },
        {
            "name": "reporting-mysql",
            "engine": "MYSQL_8_0",
            "status": "RUNNABLE",
            "tier": "db-custom-2-8192",
            "high_availability": False,
            "storage_gb": 100,
            "region": "us-central1",
            "note": "No HA — no automatic failover",
        },
    ],
}

_MOCK_CLOUD_FUNCTIONS = {
    "us-central1": [
        {"name": "process-events",       "runtime": "python312", "state": "ACTIVE"},
        {"name": "send-notifications",   "runtime": "nodejs20",  "state": "ACTIVE"},
        {"name": "cleanup-expired-data", "runtime": "python312", "state": "ACTIVE"},
    ],
}

_MOCK_DESCRIBE = {
    "cloud_run/notification-svc": {
        "name": "notification-svc",
        "region": "us-central1",
        "status": "ACTIVE",
        "instances": 1,
        "min_instances": 2,
        "revision": "notification-svc-00003",
        "platform": "managed",
        "cpu": "1",
        "memory": "512Mi",
        "recent_events": [
            {
                "time": "2025-02-20T14:05:00Z",
                "message": "Revision notification-svc-00003 is not ready: container crashed with exit code 1.",
            },
            {
                "time": "2025-02-20T14:04:00Z",
                "message": "Revision notification-svc-00003: instance scaled down due to health check failure.",
            },
        ],
    },
    "cloud_run/api-gateway-svc": {
        "name": "api-gateway-svc",
        "region": "us-central1",
        "status": "ACTIVE",
        "instances": 3,
        "min_instances": 3,
        "revision": "api-gateway-svc-00042",
        "platform": "managed",
        "cpu": "2",
        "memory": "1Gi",
        "recent_events": [],
    },
}


# ---------------------------------------------------------------------------
# TOOL 1 — list_gcp_resources
# ---------------------------------------------------------------------------

def list_gcp_resources(service_type: str, region: str = "us-central1") -> str:
    """
    List running GCP resources of the specified type in a region.

    Use this tool whenever you need to know what is currently deployed.
    Never guess or rely on prior knowledge — always call this tool first.

    Parameters
    ----------
    service_type : str
        One of: "cloud_run", "compute", "cloud_sql", "cloud_functions"
    region : str
        GCP region to query. Default: "us-central1"

    Returns
    -------
    str
        JSON list of resources with status information.
    """
    svc = service_type.lower().strip()

    if _MOCK:
        mock_map = {
            "cloud_run": _MOCK_CLOUD_RUN,
            "compute": _MOCK_GCE,
            "cloud_sql": _MOCK_CLOUD_SQL,
            "cloud_functions": _MOCK_CLOUD_FUNCTIONS,
        }
        if svc not in mock_map:
            return _wrap({"error": f"Unknown service_type '{svc}'", "supported": list(mock_map)}, "list_gcp_resources")
        items = mock_map[svc].get(region, mock_map[svc].get("us-central1", []))
        return _wrap({"service_type": svc, "region": region, "count": len(items), "resources": items}, "list_gcp_resources")

    # --- live GCP ---
    try:
        if svc == "cloud_run":
            return _live_list_cloud_run(region)
        elif svc == "compute":
            return _live_list_compute(region)
        elif svc == "cloud_sql":
            return _live_list_cloud_sql(region)
        elif svc == "cloud_functions":
            return _live_list_cloud_functions(region)
        else:
            return _wrap({"error": f"Unsupported service_type: '{svc}'"}, "list_gcp_resources")
    except Exception as exc:
        return _wrap({"error": str(exc)}, "list_gcp_resources")


def _live_list_cloud_run(region: str) -> str:
    from google.cloud import run_v2
    client = run_v2.ServicesClient()
    parent = f"projects/{_project()}/locations/{region}"
    resources = []
    for svc in client.list_services(parent=parent):
        resources.append({
            "name": svc.name.split("/")[-1],
            "region": region,
            "status": "ACTIVE" if svc.conditions else "UNKNOWN",
            "revision": svc.latest_ready_revision.split("/")[-1] if svc.latest_ready_revision else "N/A",
        })
    return _wrap({"service_type": "cloud_run", "region": region, "count": len(resources), "resources": resources}, "list_gcp_resources")


def _live_list_compute(region: str) -> str:
    from google.cloud import compute_v1
    client = compute_v1.InstancesClient()
    resources = []
    request = compute_v1.AggregatedListInstancesRequest(project=_project())
    for zone, instances_scoped_list in client.aggregated_list(request=request):
        if not zone.startswith(f"zones/{region}"):
            continue
        for inst in instances_scoped_list.instances or []:
            resources.append({
                "id": str(inst.id),
                "name": inst.name,
                "machine_type": inst.machine_type.split("/")[-1],
                "status": inst.status,
                "zone": zone.split("/")[-1],
            })
    return _wrap({"service_type": "compute", "region": region, "count": len(resources), "resources": resources}, "list_gcp_resources")


def _live_list_cloud_sql(region: str) -> str:
    from googleapiclient.discovery import build
    service = build("sqladmin", "v1beta4")
    result = service.instances().list(project=_project()).execute()
    resources = [
        {
            "name": db["name"],
            "engine": db["databaseVersion"],
            "status": db["state"],
            "tier": db["settings"]["tier"],
            "high_availability": db["settings"].get("availabilityType") == "REGIONAL",
            "storage_gb": int(db["settings"]["dataDiskSizeGb"]),
            "region": db.get("region", region),
        }
        for db in result.get("items", [])
        if db.get("region", "") == region
    ]
    return _wrap({"service_type": "cloud_sql", "region": region, "count": len(resources), "resources": resources}, "list_gcp_resources")


def _live_list_cloud_functions(region: str) -> str:
    from google.cloud import functions_v2
    client = functions_v2.FunctionServiceClient()
    parent = f"projects/{_project()}/locations/{region}"
    resources = [
        {
            "name": fn.name.split("/")[-1],
            "runtime": fn.build_config.runtime if fn.build_config else "N/A",
            "state": fn.state.name,
        }
        for fn in client.list_functions(parent=parent)
    ]
    return _wrap({"service_type": "cloud_functions", "region": region, "count": len(resources), "resources": resources}, "list_gcp_resources")


# ---------------------------------------------------------------------------
# TOOL 2 — describe_resource
# ---------------------------------------------------------------------------

def describe_resource(service_type: str, resource_name: str, region: str = "us-central1") -> str:
    """
    Get detailed configuration and recent events for a specific GCP resource.

    Use this after list_gcp_resources identifies something worth investigating.
    Provides much more detail than the listing — including recent events,
    revision history, and configuration parameters.

    Parameters
    ----------
    service_type : str
        One of: "cloud_run", "compute", "cloud_sql"
    resource_name : str
        Service name (Cloud Run), instance name (Compute Engine),
        or instance name (Cloud SQL).
    region : str
        GCP region. Default: "us-central1"

    Returns
    -------
    str
        JSON with full resource details, recent events, and configuration.
    """
    if _MOCK:
        key = f"{service_type.lower()}/{resource_name}"
        data = _MOCK_DESCRIBE.get(key)
        if data:
            return _wrap(data, "describe_resource")
        return _wrap(
            {"error": f"Resource '{resource_name}' ({service_type}) not found in {region}",
             "hint": "Use list_gcp_resources to discover available resources."},
            "describe_resource",
        )

    # --- live GCP ---
    try:
        if service_type.lower() == "cloud_run":
            return _live_describe_cloud_run(resource_name, region)
        elif service_type.lower() == "compute":
            return _live_describe_compute(resource_name, region)
        elif service_type.lower() == "cloud_sql":
            return _live_describe_cloud_sql(resource_name, region)
        else:
            return _wrap({"error": f"Unsupported service_type: '{service_type}'"}, "describe_resource")
    except Exception as exc:
        return _wrap({"error": str(exc)}, "describe_resource")


def _live_describe_cloud_run(service_name: str, region: str) -> str:
    from google.cloud import run_v2
    client = run_v2.ServicesClient()
    name = f"projects/{_project()}/locations/{region}/services/{service_name}"
    svc = client.get_service(name=name)
    return _wrap({
        "name": svc.name.split("/")[-1],
        "region": region,
        "status": "ACTIVE" if svc.conditions else "UNKNOWN",
        "revision": svc.latest_ready_revision.split("/")[-1] if svc.latest_ready_revision else "N/A",
        "uri": svc.uri,
        "recent_events": [],
    }, "describe_resource")


def _live_describe_compute(instance_name: str, region: str) -> str:
    from google.cloud import compute_v1
    client = compute_v1.InstancesClient()
    zones_client = compute_v1.ZonesClient()
    for zone in zones_client.list(project=_project()):
        if not zone.name.startswith(region):
            continue
        try:
            inst = client.get(project=_project(), zone=zone.name, instance=instance_name)
            return _wrap({
                "id": str(inst.id), "name": inst.name,
                "machine_type": inst.machine_type.split("/")[-1],
                "status": inst.status, "zone": zone.name,
                "network_interfaces": [
                    {"network": ni.network.split("/")[-1], "internal_ip": ni.network_i_p}
                    for ni in inst.network_interfaces
                ],
            }, "describe_resource")
        except Exception:
            continue
    return _wrap({"error": f"Instance '{instance_name}' not found in {region}"}, "describe_resource")


def _live_describe_cloud_sql(instance_name: str, region: str) -> str:
    from googleapiclient.discovery import build
    service = build("sqladmin", "v1beta4")
    db = service.instances().get(project=_project(), instance=instance_name).execute()
    return _wrap({
        "name": db["name"],
        "engine": db["databaseVersion"],
        "status": db["state"],
        "tier": db["settings"]["tier"],
        "high_availability": db["settings"].get("availabilityType") == "REGIONAL",
        "storage_gb": int(db["settings"]["dataDiskSizeGb"]),
        "region": db.get("region", region),
        "ip_addresses": db.get("ipAddresses", []),
        "backup_enabled": db["settings"].get("backupConfiguration", {}).get("enabled", False),
        "deletion_protection": db.get("settings", {}).get("deletionProtectionEnabled", False),
    }, "describe_resource")


# ---------------------------------------------------------------------------
# TOOL 3 — check_resource_health
# ---------------------------------------------------------------------------

def check_resource_health(service_type: str, resource_name: str, region: str = "us-central1") -> str:
    """
    Evaluate the health of a specific GCP resource and return a structured
    health report with findings and recommended actions.

    This tool synthesises raw GCP data into an opinionated assessment:
      - healthy  : resource is operating normally
      - degraded : resource is running but has issues
      - critical : resource is down or severely impaired

    Use this when you need to give a definitive health verdict rather than
    just listing raw state. Recommended next step: request_human_review if
    the status is degraded or critical.

    Parameters
    ----------
    service_type : str
        One of: "cloud_run", "compute", "cloud_sql"
    resource_name : str
        Name or ID of the resource.
    region : str
        GCP region. Default: "us-central1"

    Returns
    -------
    str
        JSON health report: status, findings list, recommendations list.
    """
    if _MOCK:
        return _mock_health(service_type, resource_name, region)

    raw = describe_resource(service_type, resource_name, region)
    detail = json.loads(raw)["data"]
    if "error" in detail:
        return _wrap({"health": "unknown", "error": detail["error"]}, "check_resource_health")
    return _derive_health(service_type, resource_name, detail, region)


def _mock_health(svc: str, name: str, region: str) -> str:
    catalog = {
        ("cloud_run", "api-gateway-svc"): {
            "health": "healthy",
            "findings": [
                "✅ Running instances (3) match minimum instances (3)",
                "✅ No recent revision failures",
                "✅ Latest revision is serving traffic",
            ],
            "recommendations": [],
        },
        ("cloud_run", "auth-service"): {
            "health": "healthy",
            "findings": [
                "✅ Running instances (2) match minimum instances (2)",
                "✅ No recent events to report",
            ],
            "recommendations": [],
        },
        ("cloud_run", "notification-svc"): {
            "health": "degraded",
            "findings": [
                "⚠️  Running instances (1) below minimum instances (2) — 50% capacity",
                "⚠️  Recent event: container crashed with exit code 1",
                "⚠️  Health check failures detected on latest revision",
            ],
            "recommendations": [
                "Check Cloud Logging for the notification-svc container logs",
                "Review CPU/memory limits — currently 1 vCPU / 512Mi (may be undersized)",
                "Inspect container exit code in Cloud Run revision details",
                "Use request_human_review to escalate for immediate investigation",
            ],
        },
        ("cloud_sql", "reporting-mysql"): {
            "health": "degraded",
            "findings": [
                "⚠️  No HA configuration — no automatic failover if instance fails",
                "ℹ️  Database is running but not production-hardened",
            ],
            "recommendations": [
                "Enable High Availability (regional) for production workloads",
                "Use request_human_review to schedule the upgrade during maintenance window",
            ],
        },
        ("cloud_sql", "prod-postgres-01"): {
            "health": "healthy",
            "findings": [
                "✅ Database status: RUNNABLE",
                "✅ High Availability enabled — automatic failover configured",
            ],
            "recommendations": [],
        },
    }
    key = (svc.lower(), name)
    data = catalog.get(key, {
        "health": "unknown",
        "findings": [f"Resource '{name}' ({svc}) not found in mock data"],
        "recommendations": ["Use list_gcp_resources to discover available resources"],
    })
    return _wrap({"resource": name, "service_type": svc, "region": region, **data}, "check_resource_health")


def _derive_health(svc: str, name: str, detail: dict, region: str) -> str:
    findings: list[str] = []
    recommendations: list[str] = []
    health = "healthy"

    if svc == "cloud_run":
        instances = detail.get("instances", 0)
        min_instances = detail.get("min_instances", 0)
        if instances < min_instances:
            health = "degraded" if instances > 0 else "critical"
            findings.append(f"⚠️  Running ({instances}) < Minimum ({min_instances})")
            recommendations.append("Check Cloud Logging for container crash details")
        else:
            findings.append(f"✅ Running ({instances}) >= Minimum ({min_instances})")
        for evt in detail.get("recent_events", [])[:3]:
            msg = evt.get("message", "")
            if any(w in msg.lower() for w in ("fail", "error", "crash", "exit")):
                health = "degraded" if health == "healthy" else health
                findings.append(f"⚠️  Event: {msg[:120]}")

    elif svc == "compute":
        status = detail.get("status", "")
        if status == "RUNNING":
            findings.append("✅ Instance is running")
        else:
            health = "critical" if status == "TERMINATED" else "degraded"
            findings.append(f"⚠️  Instance status: {status}")

    elif svc == "cloud_sql":
        status = detail.get("status", "")
        if status == "RUNNABLE":
            findings.append("✅ Database is running")
        else:
            health = "critical" if status in ("FAILED", "SUSPENDED") else "degraded"
            findings.append(f"⚠️  Database status: {status}")
        if not detail.get("high_availability"):
            findings.append("ℹ️  No HA — no automatic failover")
            recommendations.append("Consider enabling High Availability for production")

    return _wrap(
        {"resource": name, "service_type": svc, "region": region,
         "health": health, "findings": findings, "recommendations": recommendations},
        "check_resource_health",
    )


# ---------------------------------------------------------------------------
# TOOL 4 — get_environment_summary
# ---------------------------------------------------------------------------

def get_environment_summary(region: str = "us-central1") -> str:
    """
    Get a high-level summary of the infrastructure environment in a region.

    This tool aggregates across all service types to give a single-pane-of-glass
    view. Use it as a starting point when you need to orient yourself before
    drilling into specific resources.

    Unlike listing individual service types, this gives you cross-service
    context so you can identify patterns (e.g. a Cloud Run service failing to
    connect to a Cloud SQL database that is also in a degraded state).

    Parameters
    ----------
    region : str
        GCP region to summarise. Default: "us-central1"

    Returns
    -------
    str
        JSON summary: resource counts, health indicators, and action items.
    """
    if _MOCK:
        return _wrap({
            "region": region,
            "project": _project(),
            "services": {
                "cloud_run":       {"total": 4, "healthy": 3, "degraded": 1, "issues": ["notification-svc running 1/2 instances"]},
                "compute":         {"total": 4, "running": 3, "terminated": 1, "issues": ["dev-sandbox is terminated"]},
                "cloud_sql":       {"total": 2, "runnable": 2,                 "issues": ["reporting-mysql has no HA"]},
                "cloud_functions": {"total": 3, "active": 3,                   "issues": []},
            },
            "overall_health": "degraded",
            "action_items": [
                "HIGH: notification-svc is at 50% capacity — container crash detected",
                "LOW:  reporting-mysql has no HA — no automatic failover",
                "INFO: dev-sandbox Compute instance is terminated — confirm intentional",
            ],
        }, "get_environment_summary")

    summary: dict[str, Any] = {"region": region, "project": _project(), "services": {}, "action_items": []}
    overall = "healthy"
    for svc in ["cloud_run", "compute", "cloud_sql", "cloud_functions"]:
        try:
            raw = list_gcp_resources(svc, region)
            data = json.loads(raw)["data"]
            summary["services"][svc] = {"total": data.get("count", 0)}
        except Exception as exc:
            summary["services"][svc] = {"error": str(exc)}
            overall = "unknown"
    summary["overall_health"] = overall
    return _wrap(summary, "get_environment_summary")


# ---------------------------------------------------------------------------
# TOOL 5 — request_human_review
# ---------------------------------------------------------------------------

def request_human_review(
    issue_summary: str,
    urgency: str,
    full_context: str,
    recommended_action: str,
) -> str:
    """
    Escalate an issue or proposed action to a human engineer for review.

    This is the Human-in-the-Loop pattern. In Module 1, ALL write operations
    MUST go through this tool — the agent never modifies infrastructure directly.

    Use this tool when you have:
      - Identified a problem that needs fixing (degraded/critical health)
      - A recommendation that would require a GCP API write call
      - Uncertainty that warrants human judgment before proceeding

    In future modules this escalation will integrate with Pub/Sub notifications,
    Slack, and an async approval workflow. In Module 1 it logs a structured
    review record with a unique ticket ID.

    Parameters
    ----------
    issue_summary : str
        One-sentence description of the issue or proposed action.
    urgency : str
        One of: "critical", "high", "medium", "low"
    full_context : str
        All relevant findings from your investigation. Include tool outputs,
        service names, metrics, and anything a human reviewer would need.
    recommended_action : str
        Specific, actionable steps you recommend the engineer take.

    Returns
    -------
    str
        JSON confirmation with ticket_id, status, and reviewer instructions.
    """
    urgency_norm = urgency.lower().strip()
    if urgency_norm not in {"critical", "high", "medium", "low"}:
        urgency_norm = "medium"

    ticket_id = f"INFRA-{int(time.time())}"
    record = {
        "ticket_id": ticket_id,
        "status": "PENDING_HUMAN_REVIEW",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "urgency": urgency_norm.upper(),
        "issue_summary": issue_summary,
        "full_context": full_context,
        "recommended_action": recommended_action,
        "raised_by": "infrastructure-agent/module-1",
        "reviewer_note": (
            f"Review ticket {ticket_id}. "
            "Approve and execute the recommended action, or reject with a reason. "
            "Context and recommended steps are included above."
        ),
    }

    border = "=" * 62
    print(f"\n{border}")
    print(f"  🔔  HUMAN REVIEW REQUIRED  [{urgency_norm.upper()}]  {ticket_id}")
    print(border)
    print(f"  Issue   : {issue_summary}")
    print(f"  Action  : {recommended_action[:120]}{'...' if len(recommended_action) > 120 else ''}")
    print(f"  Context : {full_context[:200]}{'...' if len(full_context) > 200 else ''}")
    print(f"{border}\n")

    return _wrap(record, "request_human_review")


# ---------------------------------------------------------------------------
# Tool registry — imported by agent.py
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    list_gcp_resources,
    describe_resource,
    check_resource_health,
    get_environment_summary,
    request_human_review,
]
