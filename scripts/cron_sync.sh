#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/Users/secretagentnovi453/.openclaw/workspace-orchestrator/dummy-website"
ENV_FILE="/Users/secretagentnovi453/.openclaw/workspace-orchestrator/.env"

cd "$REPO_DIR"
python3 scripts/update_metrics.py

if git diff --quiet -- metrics.json; then
  echo "no metric changes"
  exit 0
fi

git add metrics.json
git commit -m "chore(metrics): auto-update dashboard metrics"

TOKEN=$(grep '^GITHUB_INSTALLATION_TOKEN=' "$ENV_FILE" | cut -d= -f2-)
B64=$(python3 - <<'PY'
import base64, os
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
