#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/secretagentnovi453/.openclaw/workspace-orchestrator/dummy-website"
ENV_FILE="/Users/secretagentnovi453/.openclaw/workspace-orchestrator/.env"

cd "$REPO_DIR"
python3 scripts/update_metrics.py

# Commit only if latest and previous CSV rows differ in at least one metric
# (ignore UniqueId and DateTimeStamp differences).
if ! python3 - <<'PY'
import csv
from pathlib import Path

p = Path('MetricHistory.csv')
if not p.exists():
    raise SystemExit(0)

with p.open(newline='') as f:
    rows = list(csv.DictReader(f))

# If we don't have 2 rows yet, allow commit for initialization.
if len(rows) < 2:
    raise SystemExit(0)

latest = rows[-1]
prev = rows[-2]
ignore = {'UniqueId', 'DateTimeStamp'}

changed = any(latest.get(k) != prev.get(k) for k in latest.keys() if k not in ignore)
# exit 0 means commit needed, exit 1 means skip commit
raise SystemExit(0 if changed else 1)
PY
then
  echo "no metric value changes; skipping commit"
  git checkout -- metrics.json MetricHistory.csv
  exit 0
fi

git add metrics.json MetricHistory.csv
git commit -m "chore(metrics): auto-update dashboard metrics"

TOKEN=$(grep '^GITHUB_INSTALLATION_TOKEN=' "$ENV_FILE" | cut -d= -f2-)
B64=$(python3 - <<'PY'
import base64
from pathlib import Path
env_path=Path('/Users/secretagentnovi453/.openclaw/workspace-orchestrator/.env')
token=''
for line in env_path.read_text().splitlines():
    if line.startswith('GITHUB_INSTALLATION_TOKEN='):
        token=line.split('=',1)[1].strip()
        break
print(base64.b64encode(f"x-access-token:{token}".encode()).decode())
PY
)

git -c http.extraheader="Authorization: Basic $B64" push origin main
