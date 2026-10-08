from langchain_core.tools import tool
import json
import csv
from datetime import datetime, timedelta

MOCK_DATA_DIR = "mock_data"


def _parse_since(since: str) -> timedelta:
    unit = since[-1]
    value = int(since[:-1])
    if unit == "h":
        return timedelta(hours=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        raise ValueError(f"Unsupported time unit in since='{since}'")


@tool
def get_logs(service: str, since: str = "1h") -> str:
    """Get recent log lines for a service. Use this first when investigating an issue."""
    matched = []
    with open(f"{MOCK_DATA_DIR}/logs.txt", "r") as f:
        for line in f:
            if service in line:
                matched.append(line.strip())
    if not matched:
        return f"No logs found for service '{service}'."
    return "\n".join(matched)


@tool
def get_metrics(service: str, since: str = "1h") -> str:
    """Get CPU, latency, and error rate metrics for a service over a time window."""
    matched = []
    with open(f"{MOCK_DATA_DIR}/metrics.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["service"] == service:
                matched.append(row)
    if not matched:
        return f"No metrics found for service '{service}'."
    lines = [
        f"{r['timestamp']} | cpu={r['cpu']}% | latency={r['latency_ms']}ms | error_rate={r['error_rate']}%"
        for r in matched
    ]
    return "\n".join(lines)


@tool
def get_recent_deploys(service: str) -> str:
    """Get recent deployment history for a service, including commit and author."""
    with open(f"{MOCK_DATA_DIR}/deploys.json", "r") as f:
        deploys = json.load(f)
    matched = [d for d in deploys if d["service"] == service]
    if not matched:
        return f"No recent deploys found for service '{service}'."
    lines = [
        f"{d['timestamp']} | commit={d['commit']} | author={d['author']} | \"{d['message']}\""
        for d in matched
    ]
    return "\n".join(lines)


@tool
def get_open_incidents(service: str) -> str:
    """Check whether there is already a known, tracked open incident for a service."""
    with open(f"{MOCK_DATA_DIR}/incidents.json", "r") as f:
        incidents = json.load(f)
    matched = [i for i in incidents if i["service"] == service and i["status"] == "open"]
    if not matched:
        return f"No open incidents for service '{service}'."
    lines = [
        f"{i['incident_id']} | severity={i['severity']} | opened={i['opened_at']} | {i['summary']}"
        for i in matched
    ]
    return "\n".join(lines)

@tool
def check_deploy_correlation(service: str, issue_timestamp: str) -> str:
    """Given a service and the timestamp an issue started (ISO format, e.g. 
    '2026-09-24T10:15:00Z'), returns the exact time gap in minutes between 
    the issue and the nearest deploy. Always use this instead of calculating 
    the gap yourself."""
    from datetime import datetime
    with open(f"{MOCK_DATA_DIR}/deploys.json", "r") as f:
        deploys = json.load(f)
    matched = [d for d in deploys if d["service"] == service]
    if not matched:
        return f"No deploys found for service '{service}'."

    issue_dt = datetime.fromisoformat(issue_timestamp.replace("Z", "+00:00"))
    results = []
    for d in matched:
        deploy_dt = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
        gap_minutes = abs((issue_dt - deploy_dt).total_seconds() / 60)
        results.append(f"commit={d['commit']} | gap={gap_minutes:.0f} minutes")
    return "\n".join(results)

@tool
def get_oncall_person(service: str, timestamp: str) -> str:
    """Given a service and an ISO timestamp, finds who is on-call for that 
    service's owning team at that time. Returns 'NO_ONE_ON_SHIFT' if there's 
    a gap in the schedule."""
    with open(f"{MOCK_DATA_DIR}/service_ownership.json", "r") as f:
        ownership = json.load(f)
    team = ownership.get(service)
    if not team:
        return f"No owning team found for service '{service}'."

    with open(f"{MOCK_DATA_DIR}/oncall_schedule.json", "r") as f:
        schedule = json.load(f)

    check_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    for shift in schedule:
        if shift["team"] != team:
            continue
        start = datetime.fromisoformat(shift["shift_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(shift["shift_end"].replace("Z", "+00:00"))
        if start <= check_dt < end:
            return f"{shift['member']} (slack_id={shift['slack_id']}) is on-call for {team}"

    return "NO_ONE_ON_SHIFT"


def get_nearest_upcoming_shift(service: str, timestamp: str) -> dict | None:
    """Non-tool helper: finds the next person scheduled after a gap, for fallback alerting."""
    with open(f"{MOCK_DATA_DIR}/service_ownership.json", "r") as f:
        ownership = json.load(f)
    team = ownership.get(service)
    if not team:
        return None

    with open(f"{MOCK_DATA_DIR}/oncall_schedule.json", "r") as f:
        schedule = json.load(f)

    check_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    future_shifts = [
        s for s in schedule
        if s["team"] == team and datetime.fromisoformat(s["shift_start"].replace("Z", "+00:00")) > check_dt
    ]
    if not future_shifts:
        return None
    future_shifts.sort(key=lambda s: s["shift_start"])
    return future_shifts[0]

@tool
def get_all_services_status() -> str:
    """Checks all known services and returns a brief status summary for each 
    (healthy or has an issue) based on latest metrics. Use this when asked 
    about overall system status or 'which services have issues' rather than 
    checking one service at a time."""
    latest = {}
    with open(f"{MOCK_DATA_DIR}/metrics.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            svc = row["service"]
            if svc not in latest or row["timestamp"] > latest[svc]["timestamp"]:
                latest[svc] = row

    if not latest:
        return "No services found in metrics data."

    lines = []
    for svc, row in latest.items():
        error_rate = float(row["error_rate"])
        latency = float(row["latency_ms"])
        status = "ISSUE" if (error_rate > 2.0 or latency > 300) else "healthy"
        lines.append(f"{svc}: {status} (error_rate={error_rate}%, latency={latency}ms, as of {row['timestamp']})")
    return "\n".join(lines)