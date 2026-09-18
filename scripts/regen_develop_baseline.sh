#!/usr/bin/env bash
# Regenerate the parity goldens from *develop's* engines.
#
# The goldens under tests/test_data/goldens/expected/test_develop_parity/ must be produced
# by the code we are comparing against, not by the branch being tested - otherwise they
# prove nothing. Only two files differ from develop, so they are swapped in temporarily
# rather than checking out a whole worktree.
#
# Only tracked file *content* is swapped and restored; no path is ever deleted, per the
# agent rules in CLAUDE.md.
#
# Usage:
#     bash scripts/regen_develop_baseline.sh [git-ref]      # default ref: origin/develop
#
# Afterwards, review `git diff tests/test_data/goldens/` and then confirm the suite passes
# against the new baseline with the branch's own code:
#     uv run pytest -m "not gui" -q

set -euo pipefail

REF="${1:-origin/develop}"
ENGINES=(olaf/processing/blank_correction.py olaf/processing/graph_data_csv.py)

cd "$(dirname "$0")/.."

if [[ -n "$(git status --porcelain -- "${ENGINES[@]}")" ]]; then
    echo "error: ${ENGINES[*]} have uncommitted changes." >&2
    echo "       Commit or stash them first - this script overwrites and restores them." >&2
    exit 1
fi

if ! git rev-parse --verify --quiet "$REF" >/dev/null; then
    echo "error: git ref '$REF' not found. Fetch it first (git fetch origin develop)." >&2
    exit 1
fi

restore() {
    echo
    echo "Restoring branch engines..."
    git checkout HEAD -- "${ENGINES[@]}"
    if [[ -n "$(git status --porcelain -- "${ENGINES[@]}")" ]]; then
        echo "WARNING: ${ENGINES[*]} are still modified - check 'git status'." >&2
    else
        echo "  restored cleanly."
    fi
}
trap restore EXIT

echo "Swapping in engines from $REF ($(git rev-parse --short "$REF"))..."
git checkout "$REF" -- "${ENGINES[@]}"

echo "Regenerating parity goldens (expect SKIPS, not passes - that is how regen reports)..."
# The direct-parity class compares develop against itself while the swap is in place, which
# proves nothing, so it is deselected here.
OLAF_REGEN_GOLDEN=1 uv run pytest tests/test_integration/test_develop_parity.py -q \
    -k "not Direct" || true

trap - EXIT
restore

echo
echo "Golden changes:"
git status --short tests/test_data/goldens/ || true
echo
echo "Next: review the diff above, then run"
echo "    uv run pytest -m \"not gui\" -q"
echo "Every parity test must now pass against this develop-generated baseline."
