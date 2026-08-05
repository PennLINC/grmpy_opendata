#!/bin/bash
# Upload /cbica/projects/grmpy/data/derivatives/fmriprep_anat to OpenNeuro from CUBIC.
#
# Run inside a screen session as the grmpy project user:
#     screen -S onupload
#     bash /cbica/projects/grmpy/code/openneuro/fmriprep_anat/upload-fmriprep-anat.sh
#     (detach with ctrl-a d, reattach with `screen -r onupload`)
#
# FIRST RUN:  leave DATASET empty -> creates a new accession (--new).
# RESUME:     set DATASET to the accession the first run reported. Keys already
#             stored on the remote are skipped, so a resume costs staging time
#             but not re-transfer.
DATASET=""

set -o pipefail

CLI=/cbica/projects/grmpy/openneuro-cli-batched
DATA=/cbica/projects/grmpy/data/derivatives/fmriprep_anat
OUT=/cbica/projects/grmpy/code/openneuro/fmriprep_anat
KEEP=/cbica/projects/grmpy/openneuro-worktree
LOG=$OUT/upload_$(date +%Y%m%d_%H%M%S).log

# ---------------------------------------------------------------- preflight --
eval "$(micromamba shell hook -s bash)" || { echo "micromamba hook failed"; exit 1; }
micromamba activate openneuro || { echo "could not activate the openneuro env"; exit 1; }

command -v deno >/dev/null || { echo "deno not on PATH after activating openneuro"; exit 1; }
[ -f "$CLI/mod.ts" ]       || { echo "patched CLI not found at $CLI"; exit 1; }
[ -d "$DATA" ]             || { echo "dataset not found at $DATA"; exit 1; }
[ -w "$OUT" ]              || { echo "cannot write logs to $OUT"; exit 1; }
[ -f "$HOME/.config/openneuro/config.json" ] || {
  echo "no OpenNeuro credentials for this user - run: openneuro login"; exit 1; }

# --no-lock: the repo's deno.lock is a v5 lockfile written by Deno 2.9. An older
# Deno rejects it with "Unsupported lockfile version '5'". We run from a known
# source tree, so skipping the lockfile is fine.
DENO_RUN=(deno run --allow-all --no-lock --config "$CLI/deno.json")

# Smoke-test the CLI before committing to a multi-hour run - this catches
# version, permission and import problems in seconds rather than after staging.
if ! "${DENO_RUN[@]}" "$CLI/mod.ts" --version >/dev/null 2>"$OUT/.preflight.err"; then
  echo "the CLI failed to start:"
  sed 's/^/    /' "$OUT/.preflight.err" | tail -5
  echo "  deno: $(deno --version | head -1)"
  exit 1
fi
rm -f "$OUT/.preflight.err"

# Each screen session gets its own TMPDIR (e.g. /scratch/grmpy/tmp.XXXXXXXX) and
# the CLI builds its working repo there. It disappears with the session, so the
# git dir is copied out at the end - see below.
: "${TMPDIR:=/tmp}"
export TMPDIR
export OPENNEURO_LOG=INFO
export DENO_DIR="$TMPDIR/deno" && mkdir -p "$DENO_DIR"

if [ -n "$DATASET" ]; then TARGET=(--dataset "$DATASET"); else TARGET=(--new); fi

echo "CLI:     $CLI  (5.4.0 + annex single-commit patch + batched add)"
echo "dataset: $DATA"
echo "target:  ${TARGET[*]}"
echo "TMPDIR:  $TMPDIR"
echo "log:     $LOG"
echo

# ------------------------------------------------------------ progress line --
# Output is redirected straight to a file rather than piped through `tee`. A pipe
# is what Deno was writing into when it aborted with "WouldBlock (os error 11)"
# on the parcc runs, so this avoids reintroducing that. The ticker below gives
# the same live view in the screen session without a pipe in the path.
# (If you would rather have literal tee, replace `> "$LOG" 2>&1` with
#  `2>&1 | tee "$LOG"`.)
ticker() {
  while sleep 60; do
    [ -f "$LOG" ] || continue
    printf '[%s] staged=%-7s stored=%-7s skipped=%-7s failed=%s\n' \
      "$(date +%H:%M:%S)" \
      "$(grep -cE 'INFO (Annexed|Add)' "$LOG" 2>/dev/null || echo 0)" \
      "$(grep -c 'Stored' "$LOG" 2>/dev/null || echo 0)" \
      "$(grep -c 'Skipping key' "$LOG" 2>/dev/null || echo 0)" \
      "$(grep -c 'Failed to transfer annex object' "$LOG" 2>/dev/null || echo 0)"
  done
}
ticker & TICKER=$!
trap 'kill $TICKER 2>/dev/null' EXIT

# ----------------------------------------------------------------- run it -----
"${DENO_RUN[@]}" "$CLI/mod.ts" \
  upload "${TARGET[@]}" --affirmDefaced "$DATA" > "$LOG" 2>&1
status=$?

kill $TICKER 2>/dev/null

echo
echo "=============================================================="
echo "upload exited $status"
echo "log: $LOG"
echo "  annexed:          $(grep -c 'INFO Annexed' "$LOG" || true)"
echo "  stored:           $(grep -c 'Stored' "$LOG" || true)"
echo "  skipped:          $(grep -c 'Skipping key' "$LOG" || true)"
echo "  failed transfers: $(grep -c 'Failed to transfer annex object' "$LOG" || true)"
echo "  could-not-add:    $(grep -c 'could not be added' "$LOG" || true)"
tail -3 "$LOG"

# ------------------------------------------------------- preserve the repo ----
R=$(ls -d "$TMPDIR"/openneuro_cli_*/ds* 2>/dev/null | head -1)
if [ -n "$R" ] && [ -d "$R/.git" ]; then
  DSID=$(basename "$R")
  mkdir -p "$KEEP"
  rm -rf "${KEEP:?}/${DSID}.git"
  if cp -a "$R/.git" "$KEEP/${DSID}.git"; then
    echo
    echo "accession: $DSID"
    echo "preserved: $KEEP/${DSID}.git ($(du -sh "$KEEP/${DSID}.git" | cut -f1))"
    if [ $status -ne 0 ]; then
      echo
      echo "If it failed at 'Pushing changes...', the annex content is already on"
      echo "the remote and only refs/heads/main is missing. Finish it with:"
      echo "  bash $OUT/push-main.sh $DSID"
    fi
  fi
else
  echo "WARNING: could not locate the working repo under $TMPDIR to preserve"
fi

exit $status
