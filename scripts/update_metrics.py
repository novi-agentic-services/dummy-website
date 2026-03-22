#!/usr/bin/env python3
import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "metrics.json"


def run_status_json() -> dict:
    out = subprocess.check_output(["openclaw", "status", "--usage", "--json"], text=True)
    return json.loads(out)


def compute_metrics(status: dict) -> dict:
    sessions = status.get("sessions", {}) or {}
    by_agent = sessions.get("byAgent", []) or []

    # one representative recent session per agent
    recents = [a.get("recent", [])[0] for a in by_agent if a.get("recent")]

    now = dt.datetime.now(dt.timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    active_agents = len({r.get("agentId") for r in recents if (r.get("age") or 10**9) < 300000})
    total_tasks_completed = int(sessions.get("count", 0))
    tokens_used = int(sum((r.get("totalTokens") or 0) for r in recents))
    tokens_left = int(sum((r.get("remainingTokens") or 0) for r in recents))

    today_completed = 0
    for r in recents:
        ts = r.get("updatedAt")
        if not ts:
            continue
        updated = dt.datetime.fromtimestamp(ts / 1000, tz=dt.timezone.utc)
        if updated >= day_start:
            today_completed += 1

    queued_events = status.get("queuedSystemEvents")
    queue_backlog = len(queued_events) if isinstance(queued_events, list) else int(queued_events or 0)

    token_budget = max(tokens_used + tokens_left, 1)

    return {
        "totalTasksCompleted": total_tasks_completed,
        "activeAgents": active_agents,
        "tokensUsed": tokens_used,
        "tokensLeft": tokens_left,
        "todayCompleted": today_completed,
        "queueBacklog": queue_backlog,
        "totalTasksTarget": 500,
        "activeAgentsCapacity": 25,
        "tokenBudget": token_budget,
        "dailyTasksTarget": 100,
        "queueCapacity": 50,
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    status = run_status_json()
    metrics = compute_metrics(status)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"updated {METRICS_PATH}")


if __name__ == "__main__":
    main()
