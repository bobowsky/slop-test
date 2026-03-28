#!/usr/bin/env bash
# uninstall.sh — remove machine-local generated files
# Safe: never touches roombuilder/artifacts/ or content/
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

removed=0

remove() {
    local target="$1"
    if [ -e "$target" ] || [ -L "$target" ]; then
        rm -rf "$target"
        echo "  removed  $target"
        removed=$((removed + 1))
    fi
}

echo ""
echo "VRESC uninstall — removing machine-local files"
echo "  (roombuilder/artifacts/ and content/ are untouched)"
echo ""

# Python virtual environment
remove .venv

# Python bytecode caches (anywhere in the tree except node_modules)
while IFS= read -r d; do
    remove "$d"
done < <(find . -type d -name "__pycache__" \
    -not -path "./node_modules/*" \
    -not -path "./.venv/*" \
    2>/dev/null)

# Node
remove node_modules
remove package-lock.json

# Vite build output
remove dist

echo ""
if [ "$removed" -eq 0 ]; then
    echo "  nothing to remove — already clean"
else
    echo "  $removed item(s) removed"
fi
echo ""
