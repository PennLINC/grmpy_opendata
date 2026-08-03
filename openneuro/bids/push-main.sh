#!/bin/bash
# Finish an upload whose final `git push` timed out.
#
# The CLI pushes refs/heads/main via isomorphic-git, which passes no timeout of
# its own; Deno's node-http compatibility layer imposes one that is not
# configurable and fires on large trees. System git has no such limit, so the
# same packfile goes through without trouble.
#
#   bash push-main.sh ds00XXXX
#
# Requires the .git directory preserved by upload-bids.sh. Safe to re-run.
set -euo pipefail

DSID="${1:?usage: push-main.sh <accession, e.g. ds008547>}"

eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

CLI=/cbica/projects/grmpy/openneuro-cli-patched
KEEP=/cbica/projects/grmpy/openneuro-worktree/${DSID}.git

[ -d "$KEEP" ] || { echo "no preserved git dir at $KEEP"; exit 1; }

# useHttpPath is required: the CLI's credential helper reads the accession out of
# the URL path, and git withholds the path from helpers by default.
HELPER="!deno run --allow-all --config $CLI/deno.json $CLI/mod.ts git-credential"
URL=$(git --git-dir="$KEEP" config --get remote.origin.url)
: "${URL:?could not read remote.origin.url from $KEEP}"

echo "repo:          $KEEP"
echo "remote:        $URL"
echo "local main:    $(git --git-dir="$KEEP" log -1 --format='%h %s' main)"
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
