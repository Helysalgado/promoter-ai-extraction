#!/usr/bin/env bash
# verify.sh — deterministic quality gate for promoter-ai-extraction.
# Runs the test suite; exits non-zero on any failure.
# Approved tools for this increment: pytest (ruff/mypy deferred to a later increment).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== promoter-ai-extraction — verify gate ==="
echo "Working directory: $REPO_ROOT"

# Safety: refuse to touch the real gold workbook.
if git check-ignore -q "02-DOCS/data/SUBSET_GOLD.xlsx" 2>/dev/null; then
    echo "[ok] Real gold workbook is git-ignored."
else
    echo "[WARN] Real gold workbook is NOT git-ignored — check .gitignore (T001)."
fi

# Integrity: synthetic fixtures must remain versionable.
# If the .gitignore has been broadened (e.g. to *.xlsx) it would accidentally
# exclude synthetic test fixtures — detect and fail fast.
if git check-ignore -q "tests/fixtures/synthetic_gold.xlsx" 2>/dev/null; then
    echo "[FAIL] tests/fixtures/synthetic_gold.xlsx is git-ignored."
    echo "       Synthetic fixtures must be versionable. Do not broaden .gitignore"
    echo "       to match all XLSX/XML/TXT files. Check .gitignore (T001)."
    exit 1
else
    echo "[ok] Synthetic fixture path is versionable (not git-ignored)."
fi

echo ""
echo "--- pytest ---"
uv run pytest -q "$@"

echo ""
echo "=== verify gate passed ==="
