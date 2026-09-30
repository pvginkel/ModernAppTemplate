#!/usr/bin/env bash
# Regenerate root/test-app: the root template around copies of the backend and
# frontend templates' test-apps, i.e. a complete monorepo.
#
# Usage:
#   cd /work/ModernAppTemplate/root
#   bash regen.sh
#
# Run the backend and frontend regen.sh first; this copies their test-apps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$SCRIPT_DIR"

echo "==> Removing old test-app..."
rm -rf test-app

echo "==> Running copier copy..."
(cd "$REPO_ROOT/backend" && poetry run copier copy "$REPO_ROOT" "$SCRIPT_DIR/test-app" --trust --defaults --vcs-ref HEAD \
  -d project_name=test-app \
  -d repo_name=TestApp \
  -d project_description="Test application" \
  -d author_name="Test Author" \
  -d author_email="test@example.com" \
  -d frontend_port=3000 \
  -d backend_port=5000 \
  -d sse_gateway_port=3001 \
  -d use_database=true \
  -d use_s3=true \
  -d use_sse=true)

echo "==> Copying the backend and frontend test-apps..."
for component in backend frontend; do
  if [[ ! -d "$REPO_ROOT/$component/test-app" ]]; then
    echo "Missing $REPO_ROOT/$component/test-app: run $component/regen.sh first." >&2
    exit 1
  fi
  mkdir -p "test-app/$component"
  tar -C "$REPO_ROOT/$component/test-app" --exclude=node_modules --exclude=.venv --exclude=test-results -cf - . \
    | tar -C "test-app/$component" -xf -
done
# The frontend template's .env.test points BACKEND_ROOT at ../../backend/test-app,
# its own checkout's layout. In the monorepo the default, ../backend, is right.
rm -f test-app/frontend/.env.test

echo "==> Installing root dependencies..."
cd test-app && poetry install -q

echo ""
echo "Done. Validate with:"
echo "  cd test-app"
echo "  poetry run ruff check scripts tools"
echo "  poetry run run-suite --suite backend"
