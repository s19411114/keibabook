#!/usr/bin/env bash
set -euo pipefail
HOOK_DIR=$(git rev-parse --git-dir 2>/dev/null || true)
if [ -z "$HOOK_DIR" ]; then
  echo "Not a git repository. Run this from project root with git initialized."
  exit 1
fi
PRE_COMMIT_PATH="$HOOK_DIR/hooks/pre-commit"
cat > "$PRE_COMMIT_PATH" <<'HOOK'
#!/usr/bin/env bash
# Prevent committing .bak files
if git diff --cached --name-only | grep -E '\.bak$' >/dev/null; then
  echo "Error: .bak files are not allowed to be committed. Remove them and re-add the commit." >&2
  exit 1
fi
exit 0
HOOK
chmod +x "$PRE_COMMIT_PATH"
echo "Installed pre-commit git hook to block .bak files."
