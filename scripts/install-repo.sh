#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_DIR="$PWD"
REPO_ARG=""
NO_INIT=0
FORCE=0
INIT_ARGS=()

usage() {
  cat <<'USAGE'
Install Cumulus into a repository (project-local).

Usage:
  install-repo.sh [options]

Options:
  --repo PATH           Target repository/directory (default: current repo)
  --no-init             Install runtime only; do not run interactive init
  --force               Replace an existing repo-local launcher/runtime
  --goal TEXT           Forward project goal to init
  --auto-level N        Forward optimizer autonomy level 0..3 to init
  --non-interactive     Forward non-interactive mode to init
  --yes                 Accept safe init defaults
  -h, --help            Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "ERROR: --repo requires a path" >&2; exit 2; }
      REPO_ARG="$2"; shift 2 ;;
    --no-init)
      NO_INIT=1; shift ;;
    --force)
      FORCE=1; shift ;;
    --goal)
      [[ $# -ge 2 ]] || { echo "ERROR: --goal requires text" >&2; exit 2; }
      INIT_ARGS+=("--goal" "$2"); shift 2 ;;
    --auto-level)
      [[ $# -ge 2 ]] || { echo "ERROR: --auto-level requires 0..3" >&2; exit 2; }
      INIT_ARGS+=("--auto-level" "$2"); shift 2 ;;
    --non-interactive)
      INIT_ARGS+=("--non-interactive"); shift ;;
    --yes)
      INIT_ARGS+=("--yes"); shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

command -v python3 >/dev/null 2>&1 || {
  echo "ERROR: python3 is required by v0.2.1 but was not found." >&2
  exit 1
}

if [[ -n "$REPO_ARG" ]]; then
  TARGET_START="$(cd "$REPO_ARG" && pwd)"
else
  TARGET_START="$START_DIR"
fi

if command -v git >/dev/null 2>&1 && git -C "$TARGET_START" rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git -C "$TARGET_START" rev-parse --show-toplevel)"
else
  REPO_ROOT="$TARGET_START"
fi

RUNTIME_ROOT="$REPO_ROOT/.cumulus-runtime"
RUNTIME_DIR="$RUNTIME_ROOT/runtime"
LAUNCHER="$REPO_ROOT/cumulus"

if [[ -e "$LAUNCHER" ]] && ! grep -q "cumulus repo launcher" "$LAUNCHER" 2>/dev/null; then
  if [[ "$FORCE" -ne 1 ]]; then
    echo "ERROR: $LAUNCHER already exists and is not managed by Cumulus." >&2
    echo "Re-run with --force only if you intend to replace it." >&2
    exit 1
  fi
fi

mkdir -p "$RUNTIME_ROOT"
rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR/scripts" "$RUNTIME_DIR/references" "$RUNTIME_DIR/assets"

cp "$SOURCE_DIR/scripts/cumulus.py" "$RUNTIME_DIR/scripts/cumulus.py"
cp "$SOURCE_DIR/skills/cumulus/SKILL.md" "$RUNTIME_DIR/SKILL.md"
cp "$SOURCE_DIR/VERSION" "$RUNTIME_DIR/VERSION"
cp "$SOURCE_DIR/CHANGELOG.md" "$RUNTIME_DIR/CHANGELOG.md"
if [[ -d "$SOURCE_DIR/references" ]]; then cp -R "$SOURCE_DIR/references/." "$RUNTIME_DIR/references/"; fi
if [[ -d "$SOURCE_DIR/assets" ]]; then cp -R "$SOURCE_DIR/assets/." "$RUNTIME_DIR/assets/"; fi
chmod +x "$RUNTIME_DIR/scripts/cumulus.py"

cat > "$LAUNCHER" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
# cumulus repo launcher
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ROOT/.cumulus-runtime/runtime/scripts/cumulus.py" "$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

python3 - "$RUNTIME_ROOT/install.json" "$REPO_ROOT" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
out=Path(sys.argv[1])
repo=sys.argv[2]
data={
    "version":"0.2.1",
    "scope":"repository",
    "repository":repo,
    "installed_at":datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    "launcher":"./cumulus",
}
out.write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
PY

GITIGNORE="$REPO_ROOT/.gitignore"
BEGIN="# >>> cumulus local runtime >>>"
END="# <<< cumulus local runtime <<<"
TMP="$(mktemp)"
if [[ -f "$GITIGNORE" ]]; then
  awk -v b="$BEGIN" -v e="$END" '
    $0==b {skip=1; next}
    $0==e {skip=0; next}
    !skip {print}
  ' "$GITIGNORE" > "$TMP"
fi
{
  cat "$TMP" 2>/dev/null || true
  if [[ -s "$TMP" ]]; then printf '\n'; fi
  printf '%s\n' "$BEGIN"
  printf '.cumulus-runtime/\n'
  printf 'cumulus\n'
  printf '%s\n' "$END"
} > "$GITIGNORE"
rm -f "$TMP"

printf '\nCumulus 0.2.1 installed locally\n'
printf '  Repository : %s\n' "$REPO_ROOT"
printf '  Runtime    : .cumulus-runtime/\n'
printf '  Launcher   : ./cumulus\n'
printf '  Global install: none\n\n'

if [[ "$NO_INIT" -eq 0 ]]; then
  cd "$REPO_ROOT"
  if [[ -r /dev/tty ]] && [[ " ${INIT_ARGS[*]} " != *" --non-interactive "* ]]; then
    "$LAUNCHER" init "${INIT_ARGS[@]}" < /dev/tty
  else
    "$LAUNCHER" init "${INIT_ARGS[@]}"
  fi
else
  printf 'Initialize later with:\n  cd %q && ./cumulus init\n' "$REPO_ROOT"
fi
