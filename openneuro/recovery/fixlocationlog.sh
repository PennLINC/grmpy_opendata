#!/bin/bash
# The 63 repaired objects are on the remote, but their location log still says
# absent (0), so git-annex refuses to fetch them. Rewrite those entries.
#
#   bash fixlocationlog.sh <clone dir> <upload log>          # report only
#   bash fixlocationlog.sh <clone dir> <upload log> --fix    # rewrite + push
set -o pipefail
CLONE="${1:?usage: fixlocationlog.sh <clone> <upload log> [--fix]}"
LOG="${2:?usage: fixlocationlog.sh <clone> <upload log> [--fix]}"
FIX="${3:-}"
UUID=57538107-c452-4407-bf8d-1fca76134852
cd "$CLONE" || exit 1

echo "=== control: 5 keys that uploaded cleanly ==="
git ls-tree -r git-annex --name-only | grep '\.log$' | shuf -n 5 --random-source=/dev/zero | while read -r f; do
  printf '  %s -> %s\n' "$(basename "$f" .log | cut -c1-40)..." "$(git show "git-annex:$f" | head -1 | awk '{print $2}')"
done

mapfile -t KEYS < <(grep -ao 'Failed to transfer annex object "[^"]*"' "$LOG" | sed 's/.*object "//;s/"$//' | sort -u)
echo
echo "=== the ${#KEYS[@]} repaired keys ==="
absent=0; present=0
for k in "${KEYS[@]}"; do
  f=$(git ls-tree -r git-annex --name-only | grep -F "$k.log" | head -1)
  [ -n "$f" ] || { echo "  no log entry: $k"; continue; }
  state=$(git show "git-annex:$f" | grep -F "$UUID" | tail -1 | awk '{print $2}')
  if [ "$state" = "1" ]; then present=$((present+1)); else absent=$((absent+1)); fi
done
echo "  marked present (1): $present"
echo "  marked absent  (0): $absent"

if [ "$FIX" != "--fix" ]; then
  echo
  echo "(report only - rerun with --fix to rewrite these and push the git-annex branch)"
  exit 0
fi

echo
echo "=== rewriting location log ==="
for k in "${KEYS[@]}"; do
  git annex setpresentkey "$k" "$UUID" 1 && echo "  set present: ${k:0:50}..."
done

echo
echo "=== pushing git-annex branch ==="
CLI=/cbica/projects/grmpy/openneuro-cli-batched
git -c credential.useHttpPath=true \
    -c credential.helper="!deno run -A --no-lock --config $CLI/deno.json $CLI/mod.ts git-credential" \
    push origin git-annex
