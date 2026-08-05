#!/bin/bash
#SBATCH -J fmriprep-anat-resume
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 2-00:00:00
#SBATCH --exclude=epyc-1-2
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat/slurm_%j.log

# Resume the ds008578 upload without restaging.
#
# Job 7422202 staged all 97,841 entries and committed them, then died in
# getAnnexKeys with a bogus "Could not find <oid>" - isomorphic-git's
# FileSystem.read returns null for ANY failed read, and readObjectLoose reports
# that as a missing object. The commit and every object survived (fsck is clean
# on the preserved repo), so there is no reason to rehash 192 GB.
#
# --resume skips both the clone and the staging pass, then builds the git-annex
# branch and pushes. Nothing in that path reads the worktree.

set -o pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
# ERROR rather than INFO: the WouldBlock aborts have all landed on a per-item
# logger.info inside the worker, and the push phase makes ~90k of them.
export OPENNEURO_LOG=ERROR

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
DATA=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/fmriprep_anat
OUT=/ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat
KEEP=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-worktree/ds008578.git
LOG=$OUT/resume_${SLURM_JOB_ID}.log

# Stage the repo on node-local NVMe rather than CephFS. isomorphic-git reads
# loose objects with unbounded Promise.all fan-out; against 85k small files on a
# network filesystem that is slow and produces transient read failures, which it
# then misreports as missing objects. The copy on /ceph stays pristine as the
# fallback for another attempt.
export OPENNEURO_REPO_DIR=/tmp/on-resume-$SLURM_JOB_ID
mkdir -p "$OPENNEURO_REPO_DIR/ds008578"
echo "copying preserved repo to node-local disk..."
cp -a "$KEEP" "$OPENNEURO_REPO_DIR/ds008578/.git" || { echo "copy failed"; exit 1; }

echo "repo:    $OPENNEURO_REPO_DIR/ds008578  ($(du -sh "$OPENNEURO_REPO_DIR/ds008578/.git" | cut -f1))"
echo "commit:  $(git -C "$OPENNEURO_REPO_DIR/ds008578" log -1 --format='%h %s' main 2>&1)"
echo "log:     $LOG"
echo

deno run --allow-all --config "$CLI/deno.json" "$CLI/mod.ts" \
  upload --dataset ds008578 --resume --affirmDefaced "$DATA" > "$LOG" 2>&1
status=$?

echo "resume exited $status"
echo "  stored:           $(grep -c 'Stored' "$LOG" || true)"
echo "  skipped:          $(grep -c 'Skipping key' "$LOG" || true)"
echo "  failed transfers: $(grep -c 'Failed to transfer annex object' "$LOG" || true)"
tail -5 "$LOG"

# Refresh the /ceph copy so a later attempt starts from the newest state
# (the git-annex branch commit, if it got that far).
if [ -d "$OPENNEURO_REPO_DIR/ds008578/.git" ]; then
  rm -rf "${KEEP}.new" && cp -a "$OPENNEURO_REPO_DIR/ds008578/.git" "${KEEP}.new" &&
    rm -rf "$KEEP" && mv "${KEEP}.new" "$KEEP" && echo "refreshed preserved repo at $KEEP"
fi

exit $status
