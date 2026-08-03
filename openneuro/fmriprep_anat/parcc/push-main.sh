#!/bin/bash
# Finish an upload whose final `git push` timed out.
#
# The CLI's push of refs/heads/main uses isomorphic-git, which passes no timeout;
# Deno's node-http shim imposes one that is not configurable, and it fires on
# large trees. System git has no such limit. Run this on the login node.
#
#   ./push-main.sh ds00XXXX
#
# Requires the .git directory preserved by upload.sbatch.
set -euo pipefail

DSID="${1:?usage: push-main.sh <accession, e.g. ds008547>}"

eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro
export DENO_DIR=/tmp/deno-$USER

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
KEEP=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-worktree/${DSID}.git

[ -d "$KEEP" ] || { echo "no preserved git dir at $KEEP"; exit 1; }

# The CLI's own credential helper. useHttpPath is required: the helper reads the
# accession out of the URL path, which git withholds by default.
HELPER="!deno run --allow-all --config $CLI/deno.json $CLI/mod.ts git-credential"
URL=$(git --git-dir="$KEEP" config --get remote.origin.url)
: "${URL:?could not read remote.origin.url from $KEEP}"

echo "repo:  $KEEP"
echo "remote: $URL"
echo "local main:  $(git --git-dir="$KEEP" log -1 --format='%h %s' main)"
echo "files in main: $(git --git-dir="$KEEP" ls-tree -r main --name-only | wc -l)"
echo

git --git-dir="$KEEP" \
    -c credential.useHttpPath=true \
    -c credential.helper="$HELPER" \
    -c http.postBuffer=524288000 \
    push "$URL" main:main

echo
echo "=== remote refs now ==="
git --git-dir="$KEEP" -c credential.useHttpPath=true -c credential.helper="$HELPER" \
    ls-remote "$URL" 2>/dev/null
