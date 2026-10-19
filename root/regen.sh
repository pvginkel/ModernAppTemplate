#!/usr/bin/env bash
# Regenerate the root test-apps: the root template around copies of the backend
# and frontend templates' test-apps, i.e. complete monorepos.
#
# Two test-apps:
#   test-app             every flag on, around backend/test-app and
#                        frontend/test-app. Its suite runner runs the backend
#                        suite and, by hand, Playwright.
#   test-app-no-storage  use_database=false and use_s3=false, as DHCPApp,
#                        ZigbeeControl and FieldnotesApp run, around
#                        backend/test-app-no-storage and
#                        frontend/test-app-no-shell (two of those three apps
#                        run without the shell). Backend suite only: the
#                        frontend is never built or run here.
#
# Usage:
#   cd /work/ModernAppTemplate/root
#   bash regen.sh                        # both test-apps
#   bash regen.sh test-app-no-storage    # only the named ones
#
# Run the backend and frontend regen.sh first; this copies their test-apps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

# The sidecar's uv cache and /work are different mounts, so hardlinks fail.
export UV_LINK_MODE=copy

# regen <dir> <use_database> <use_s3> <backend test-app> <frontend test-app>
regen() {
  local app="$1" database="$2" s3="$3" backend_app="$4" frontend_app="$5"

  echo "==> [$app] Removing old test-app..."
  rm -rf "$app"

  echo "==> [$app] Running copier copy..."
  (cd "$REPO_ROOT/backend" && uv run --locked copier copy "$REPO_ROOT" "$SCRIPT_DIR/$app" --trust --defaults --vcs-ref HEAD \
    -d project_name=test-app \
    -d repo_name=TestApp \
    -d project_description="Test application" \
    -d author_name="Test Author" \
    -d author_email="test@example.com" \
    -d frontend_port=3000 \
    -d backend_port=5000 \
    -d use_database="$database" \
    -d use_s3="$s3" \
    -d use_sse=true)

  echo "==> [$app] Copying backend/$backend_app and frontend/$frontend_app..."
  local component source
  for component in backend frontend; do
    if [ "$component" = backend ]; then source="$backend_app"; else source="$frontend_app"; fi
    if [[ ! -d "$REPO_ROOT/$component/$source" ]]; then
      echo "Missing $REPO_ROOT/$component/$source: run $component/regen.sh first." >&2
      exit 1
    fi
    mkdir -p "$app/$component"
    # .git: the frontend regen makes its gitignored test-app a repo of its own.
    tar -C "$REPO_ROOT/$component/$source" --exclude=node_modules --exclude=.venv --exclude=test-results --exclude=.git -cf - . \
      | tar -C "$app/$component" -xf -
  done
  # The frontend template's .env.test points BACKEND_ROOT at ../../backend/test-app,
  # its own checkout's layout. In the monorepo the default, ../backend, is right.
  rm -f "$app/frontend/.env.test"

  if [ "$database" != true ]; then
    # The frontend's OpenAPI cache is the full backend's document, and this
    # backend documents less (no Items, no CAS), so the backend suite's
    # tests/test_openapi_cache.py would fail on it. Refresh it from this
    # backend, built as that test builds it: from the environment alone. An app
    # runs scripts/regenerate-openapi.py --frontend; that also regenerates the
    # client, which needs the frontend installed, and nothing here builds it.
    echo "==> [$app] Refreshing the frontend's OpenAPI cache from this backend..."
    (cd "$app/backend" && uv sync -q --locked && uv run python -c '
import json
import sys

from app import create_app

app = create_app(skip_background_services=True)
response = app.test_client().get("/api/docs/openapi.json")
if response.status_code != 200:
    sys.exit(f"GET /api/docs/openapi.json answered {response.status_code}")
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(response.get_json(), f, indent=2)
    f.write("\n")
' ../frontend/openapi-cache/openapi.json)
  fi

  echo "==> [$app] Installing root dependencies..."
  (cd "$app" && uv sync -q)
}

apps=("$@")
if [ ${#apps[@]} -eq 0 ]; then
  apps=(test-app test-app-no-storage)
fi

for app in "${apps[@]}"; do
  case "$app" in
    test-app) regen test-app true true test-app test-app ;;
    test-app-no-storage) regen test-app-no-storage false false test-app-no-storage test-app-no-shell ;;
    *) echo "Unknown test-app: $app (expected test-app or test-app-no-storage)" >&2; exit 2 ;;
  esac
done

echo ""
echo "Done. Validate in each regenerated test-app with:"
echo "  uv run ruff check scripts tools"
echo "  uv run run-suite --suite backend"
