#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPT="python3 $SCRIPT_DIR/cumulus.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
git init -q
git config user.email smoke@example.com
git config user.name Smoke
cat > pyproject.toml <<'EOF'
[project]
name = "optimizer-smoke"
dependencies = ["fastapi", "asyncpg", "pytest"]
EOF

$OPT init --auto-level 2 --goal "Smoke test API" >/dev/null
$OPT integrate >/dev/null
for i in 1 2 3; do
  $OPT task-start --task-id "MIG-$i" --domain database-migrations --goal "Test migration" >/dev/null
  $OPT task-end --result failed --retries 1 --effort high --manual "manual repair" --message "migration failed" >/dev/null
done
IMP="$($OPT improvements | awk -F: 'NR==1{print $1}')"
test -n "$IMP"
$OPT trial-start "$IMP" --candidate better-migration-workflow --before '{"success":0.3}' >/dev/null
$OPT trial-finish "$IMP" --outcome keep --after '{"success":0.9}' --reason "improved" >/dev/null
$OPT analyze | grep -q "No capability-debt pattern"
$OPT compact >/dev/null
$OPT doctor >/dev/null

test -f .cumulus/project.json
test -f .cumulus/capabilities.json
test -f .cumulus/skills.lock.json
grep -q "cumulus:start" AGENTS.md

echo "Cumulus v0.2 smoke test: PASS"
