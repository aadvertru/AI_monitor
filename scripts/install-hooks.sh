#!/usr/bin/env sh
set -eu

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required to install hooks."
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
  echo "Could not determine repository root. Run this inside a git repository."
  exit 1
fi

PRE_COMMIT_SCRIPT="$REPO_ROOT/scripts/pre-commit.sh"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
HOOK_PATH="$HOOKS_DIR/pre-commit"

if [ ! -f "$PRE_COMMIT_SCRIPT" ]; then
  echo "Missing pre-commit script: $PRE_COMMIT_SCRIPT"
  exit 1
fi

mkdir -p "$HOOKS_DIR"

cat > "$HOOK_PATH" <<'EOF'
#!/usr/bin/env sh
set -eu

REPO_ROOT="$(git rev-parse --show-toplevel)"
"$REPO_ROOT/scripts/pre-commit.sh"
EOF

chmod +x "$PRE_COMMIT_SCRIPT"
chmod +x "$HOOK_PATH"

echo "Installed git pre-commit hook at: $HOOK_PATH"
echo "Bypass once (if needed): git commit --no-verify"
