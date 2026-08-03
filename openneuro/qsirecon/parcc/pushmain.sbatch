#!/bin/bash
#SBATCH -J push-main
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 04:00:00
#SBATCH --nodelist=epyc-2-3
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/pushmain_%j.log

set -o pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro
export DENO_DIR=/tmp/deno-$USER

C=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
URL=https://openneuro.org/git/2/ds008547
HELPER="!deno run --allow-all --config $C/deno.json $C/mod.ts git-credential"

R=$(ls -d /tmp/openneuro_cli_*/ds008547 2>/dev/null | head -1)
echo "hostname: $(hostname)"
if [ -z "$R" ] || [ ! -d "$R/.git" ]; then
  echo "RESULT: REPO GONE - /tmp was cleaned, full re-upload required"
  exit 10
fi

echo "RESULT: REPO PRESENT at $R"
echo "size: $(du -sh "$R" 2>/dev/null | cut -f1)"
echo "--- local branches ---"
git -C "$R" show-ref | head
echo "--- files in local main ---"
LOCAL_FILES=$(git -C "$R" ls-tree -r main --name-only 2>/dev/null | wc -l)
echo "local main file count: $LOCAL_FILES"
git -C "$R" log -1 --format="local main: %H %s" main

if [ "$LOCAL_FILES" -lt 60000 ]; then
  echo "RESULT: local main does not look complete ($LOCAL_FILES files); not pushing"
  exit 11
fi

echo "=== pushing main with system git ==="
git -C "$R" -c credential.useHttpPath=true -c credential.helper="$HELPER" \
    -c http.postBuffer=524288000 \
    push "$URL" main:main
echo "push exit: $?"

echo "=== verifying remote ==="
git -C "$R" -c credential.useHttpPath=true -c credential.helper="$HELPER" \
    ls-remote "$URL" 2>/dev/null
