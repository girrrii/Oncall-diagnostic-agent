import time
import csv
import os
from dotenv import load_dotenv
from slack_sdk import WebClient

from tools import get_oncall_person, get_nearest_upcoming_shift
from agent import ask

load_dotenv()

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

THRESHOLDS = {
    "error_rate": 2.0,   # percent — breach if exceeded
    "latency_ms": 300,   # ms — breach if exceeded
}

POLL_INTERVAL_SECONDS = 30
ALREADY_ALERTED = set()  # (service, timestamp) pairs already alerted this run

FALLBACK_CHANNEL_ID = "REPLACE_WITH_CHANNEL_ID"  # e.g. C0123ABC456


def get_latest_metrics():
    """Reads metrics.csv, returns the most recent row per service."""
    latest = {}
    with open("mock_data/metrics.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            svc = row["service"]
            if svc not in latest or row["timestamp"] > latest[svc]["timestamp"]:
                latest[svc] = row
    return latest


def send_dm(slack_id, text):
    convo = client.conversations_open(users=[slack_id])
    channel_id = convo["channel"]["id"]
    client.chat_postMessage(channel=channel_id, text=text)


def handle_issue(service, timestamp):
    print(f"[MONITOR] Threshold breach: {service} at {timestamp}")

    diagnosis = ask(f"what's happening with {service}?")
    oncall_result = get_oncall_person.invoke({"service": service, "timestamp": timestamp})

    if "is on-call" in oncall_result:
        slack_id = oncall_result.split("slack_id=")[1].split(")")[0]
        member_name = oncall_result.split(" (")[0]
        message = f":rotating_light: *Alert: {service}*\n\n{diagnosis}\n\n(You're being notified because you're on-call.)"
        send_dm(slack_id, message)
        print(f"[MONITOR] Alerted {member_name} via DM")
    else:
        message = f":rotating_light: *Unattended alert: {service}*\n\nNo one is currently on-call.\n\n{diagnosis}"
        client.chat_postMessage(channel=FALLBACK_CHANNEL_ID, text=message)
        print(f"[MONITOR] No one on shift — posted to fallback channel")

        upcoming = get_nearest_upcoming_shift(service, timestamp)
        if upcoming:
            heads_up = f":alarm_clock: Heads up {upcoming['member']} — an issue was detected on {service} before your shift starts. Please check when you're on."
            send_dm(upcoming["slack_id"], heads_up)
            print(f"[MONITOR] Sent heads-up to upcoming on-call: {upcoming['member']}")


def check_thresholds():
    for service, row in get_latest_metrics().items():
        error_rate = float(row["error_rate"])
        latency = float(row["latency_ms"])
        timestamp = row["timestamp"]

        if error_rate > THRESHOLDS["error_rate"] or latency > THRESHOLDS["latency_ms"]:
            key = (service, timestamp)
            if key not in ALREADY_ALERTED:
                ALREADY_ALERTED.add(key)
                handle_issue(service, timestamp)


if __name__ == "__main__":
    print(f"On-call monitor running. Polling every {POLL_INTERVAL_SECONDS}s...")
    while True:
        check_thresholds()
        time.sleep(POLL_INTERVAL_SECONDS)