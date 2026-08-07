#!/bin/bash
# Check every key the log reported as failed, to see whether it is actually
# present on the remote.
#   bash verifyfailed.sh <upload log>
set -o pipefail
LOG="${1:?usage: verifyfailed.sh <upload log>}"
[ -f "$LOG" ] || { echo "no such log: $LOG"; exit 1; }

eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro
CLI=/cbica/projects/grmpy/openneuro-cli-batched

URL=$(grep -ao 'https://openneuro.org/git/[0-9]*/ds[0-9]*' "$LOG" | head -1)
TOK=$(printf 'protocol=https\nhost=openneuro.org\npath=%s\n\n' "${URL#https://openneuro.org/}" \
      | deno run -A --no-lock --config "$CLI/deno.json" "$CLI/mod.ts" git-credential get 2>/dev/null \
      | sed -n 's/^password=//p')
[ "${#TOK}" -ge 20 ] || { echo "token not acquired"; exit 1; }

mapfile -t KEYS < <(grep -ao 'Failed to transfer annex object "[^"]*"' "$LOG" \
                    | sed 's/.*object "//;s/"$//' | sort -u)
echo "endpoint: $URL"
echo "distinct failed keys: ${#KEYS[@]}"
echo

present=0; missing=0
for k in "${KEYS[@]}"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -u "openneuro-cli:$TOK" "$URL/annex/$k")
  if [ "$code" = "200" ]; then
    present=$((present+1))
  else
    missing=$((missing+1))
    echo "  MISSING (HTTP $code): $k"
  fi
done

echo
echo "present on remote: $present"
echo "actually missing:  $missing"
[ "$missing" -eq 0 ] && echo "=> dataset is COMPLETE; the errors were false alarms" \
                     || echo "=> $missing objects really did not upload"
