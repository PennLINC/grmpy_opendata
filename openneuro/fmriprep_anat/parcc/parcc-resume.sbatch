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
# getAnnexKeys with a bogus "Could not find <oid>" (isomorphic-git reports any
# failed read as a missing object). The commit and every object survived - fsck
# on the preserved repo is clean - so there is no reason to rehash 192 GB.
#
# --resume skips addGitFiles and triggers commitAnnexBranch directly, then
# pushes. push() streams content from $DATA, not from the working repo.

set -o pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
# ERROR rather than INFO: the WouldBlock aborts have all landed on a per-item
# logger.info inside the worker, and the push phase makes ~90k of them.
export OPENNEURO_LOG=ERROR
# Points the CLI at the restored repo instead of a fresh node-local temp dir.
export OPENNEURO_REPO_DIR=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-worktree/resume

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
DATA=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/fmriprep_anat
OUT=/ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat
LOG=$OUT/resume_${SLURM_JOB_ID}.log

echo "repo:    $OPENNEURO_REPO_DIR/ds008578"
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

exit $status