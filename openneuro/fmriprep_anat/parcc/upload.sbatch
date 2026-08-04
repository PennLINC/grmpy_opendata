#!/bin/bash
#SBATCH -J fmriprep-anat-upload
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 7-00:00:00
#SBATCH --exclude=epyc-1-2
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat/slurm_%j.log

# Upload derivatives/fmriprep_anat to OpenNeuro.
#
# FIRST RUN:  leave DATASET empty -> creates a new accession (--new).
# RESUME:     set DATASET to the accession the first run created. Keys already
#             stored on the remote are skipped, so a resume costs staging time
#             but not re-transfer.
DATASET="ds008578"

set -o pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
export OPENNEURO_LOG=ERROR

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
DATA=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/fmriprep_anat
OUT=/ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat
LOG=$OUT/upload_${SLURM_JOB_ID}.log
KEEP=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-worktree

if [ -n "$DATASET" ]; then
  TARGET=(--dataset "$DATASET")
else
  TARGET=(--new)
fi

# Output goes to a regular file rather than SLURM's stdout pipe. This is not a
# guaranteed fix - Deno can still abort with "WouldBlock (os error 11)" during
# long, high-output runs and the cause is not understood - but the job is
# recoverable either way, see the .git preservation below.
deno run --allow-all --config "$CLI/deno.json" "$CLI/mod.ts" \
  upload "${TARGET[@]}" --affirmDefaced "$DATA" > "$LOG" 2>&1
status=$?

echo "upload exited ${status}"
echo "log: ${LOG}"
echo "annexed:  $(grep -c 'INFO Annexed' "$LOG" || true)"
echo "stored:   $(grep -c 'Stored' "$LOG" || true)"
echo "skipped:  $(grep -c 'Skipping key' "$LOG" || true)"
echo "failed transfers: $(grep -c 'Failed to transfer annex object' "$LOG" || true)"

# Preserve the git directory. /tmp is node-local and wiped when the job ends, so
# without this a failed push (or a crash after staging) means re-hashing the
# whole dataset. With it, push-main.sh finishes the job in minutes.
R=$(ls -d /tmp/openneuro_cli_*/ds* 2>/dev/null | head -1)
if [ -n "$R" ] && [ -d "$R/.git" ]; then
  DSID=$(basename "$R")
  mkdir -p "$KEEP"
  rm -rf "$KEEP/${DSID}.git"
  cp -a "$R/.git" "$KEEP/${DSID}.git" &&
    echo "preserved: $KEEP/${DSID}.git ($(du -sh "$KEEP/${DSID}.git" | cut -f1))"
  echo "accession: $DSID"
else
  echo "WARNING: could not locate the working repo to preserve"
fi

exit ${status}
