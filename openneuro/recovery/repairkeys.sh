#!/bin/bash
# Upload the annex objects a run reported as failed, one at a time, printing the
# real HTTP status for each. storeKey() collapses every non-200 into -1, so this
# is the only way to see why they failed.
#
#   bash repairkeys.sh <upload log> <dataset dir> [--dry-run]
set -o pipefail

LOG="${1:?usage: repairkeys.sh <upload log> <dataset dir> [--dry-run]}"
DATA="${2:?usage: repairkeys.sh <upload log> <dataset dir> [--dry-run]}"
DRY="${3:-}"
[ -f "$LOG" ]  || { echo "no such log: $LOG"; exit 1; }
[ -d "$DATA" ] || { echo "no such dataset dir: $DATA"; exit 1; }

eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro
CLI=/cbica/projects/grmpy/openneuro-cli-batched

URL=$(grep -ao 'https://openneuro.org/git/[0-9]*/ds[0-9]*' "$LOG" | head -1)
TOK=$(printf 'protocol=https\nhost=openneuro.org\npath=%s\n\n' "${URL#https://openneuro.org/}" \
      | deno run -A --no-lock --config "$CLI/deno.json" "$CLI/mod.ts" git-credential get 2>/dev/null \
      | sed -n 's/^password=//p')
[ "${#TOK}" -ge 20 ] || { echo "token not acquired"; exit 1; }
echo "endpoint: $URL"

mapfile -t KEYS < <(grep -ao 'Failed to transfer annex object "[^"]*"' "$LOG" \
                    | sed 's/.*object "//;s/"$//' | sort -u)
echo "failed keys: ${#KEYS[@]}"

# Index the dataset by file size once, so each key only has to hash candidates
echo "indexing dataset by size..."
IDX=$(mktemp)
find "$DATA" -type f -printf '%s\t%p\n' > "$IDX"
echo "indexed $(wc -l < "$IDX") files"
echo

ok=0; fail=0; nofile=0
for k in "${KEYS[@]}"; do
  size=$(sed 's/^[A-Z0-9]*-s\([0-9]*\)--.*/\1/' <<<"$k")
  hash=$(sed 's/^[A-Z0-9]*-s[0-9]*--\([0-9a-f]*\).*/\1/' <<<"$k")
  match=""
  while IFS=$'\t' read -r sz path; do
    [ "$sz" = "$size" ] || continue
    [ "$(sha256sum "$path" | cut -d' ' -f1)" = "$hash" ] && { match="$path"; break; }
  done < "$IDX"

  if [ -z "$match" ]; then
    echo "NO LOCAL FILE for $k"; nofile=$((nofile+1)); continue
  fi
  if [ "$DRY" = "--dry-run" ]; then
    echo "would upload: $match"; continue
  fi
  code=$(curl -s -o /tmp/repair.body -w '%{http_code}' -X POST \
         -u "openneuro-cli:$TOK" -H "Content-Length: $size" \
         --data-binary "@$match" "$URL/annex/$k")
  if [ "$code" = "200" ]; then
    ok=$((ok+1)); echo "OK   $code  $(basename "$match")"
  else
    fail=$((fail+1))
    echo "FAIL $code  $(basename "$match")"
    echo "     body: $(head -c 200 /tmp/repair.body)"
  fi
done
rm -f "$IDX"
echo
echo "uploaded: $ok   failed: $fail   no local file: $nofile"
