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

    recents = [a.get("recent", [])[0] for a in by_agent if a.get("recent")]
    now = dt.datetime.now(dt.timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Consider a session "active" if updated within last 15 minutes.
    active_cutoff_ms = 15 * 60 * 1000
    active_sessions = [r for r in recents if (r.get("age") or 10**9) <= active_cutoff_ms]

    active_agents = len({r.get("agentId") for r in active_sessions if r.get("agentId")})
    active_agents_capacity = 25

    tokens_used = int(sum((r.get("totalTokens") or 0) for r in recents))
    tokens_left = int(sum((r.get("remainingTokens") or 0) for r in recents))
    token_budget = max(tokens_used + tokens_left, 1)
    tokens_used_pct = (tokens_used / token_budget) * 100

    today_completed = 0
    for r in recents:
        ts = r.get("updatedAt")
        if not ts:
            continue
        updated = dt.datetime.fromtimestamp(ts / 1000, tz=dt.timezone.utc)
        if updated >= day_start:
            today_completed += 1

    today_per_agent = (today_completed / active_agents) if active_agents > 0 else 0.0

    active_tasks = []
    for idx, r in enumerate(active_sessions[:12], start=1):
        agent = r.get('agentId', 'agent')
        kind = r.get('kind', 'task')
        active_tasks.append(
            {
                "id": f"task-{idx}",
                "description": f"{agent} handling {kind} session",
                "tokensUsed": int(r.get("totalTokens") or 0),
                "runtimeMinutes": round(((r.get("age") or 0) / 1000) / 60, 1),
            }
        )

    return {
        # Row 1: token info
        "tokensUsed": tokens_used,
        "tokensLeft": tokens_left,
        "tokenBudget": token_budget,
        "tokensUsedPct": round(tokens_used_pct, 2),

        # Row 2: agent info
        "activeAgents": active_agents,
        "activeAgentsCapacity": active_agents_capacity,
        "todayCompleted": today_completed,
        "todayCompletedPerAgent": round(today_per_agent, 2),
        "dailyTasksTarget": 100,
        "tasksPerAgentTarget": 5,

        # Row 3: detailed active tasks
        "activeTasks": active_tasks,

        "updatedAt": now.isoformat().replace("+00:00", "Z"),
    }


def main() -> None:
    status = run_status_json()
    metrics = compute_metrics(status)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"updated {METRICS_PATH}")


if __name__ == "__main__":
    main()
