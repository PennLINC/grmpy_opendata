#!/bin/bash
#SBATCH -J qsirecon-upload
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 7-00:00:00
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/slurm_%j.log

set -o pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
export OPENNEURO_LOG=INFO

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
DATA=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/qsirecon
LOG=/ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload_${SLURM_JOB_ID}.log
KEEP=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-worktree

# All 40,176 annex objects are already stored on the remote from job 7340698, and
# the git-annex branch is pushed. Only refs/heads/main is missing - the final git
# push timed out. checkKey will skip every transfer, so this run is staging + push.
#
# Output goes straight to a regular file: under SLURM, #SBATCH -o makes stdout a
# pipe to slurmstepd, Deno sets stdio pipes non-blocking, and a burst of log lines
# can kill the job with "WouldBlock (os error 11)". NOTE: this redirect reduces
# but does NOT eliminate it - it recurred on CephFS in job 7348892.
deno run --allow-all --config "$CLI/deno.json" "$CLI/mod.ts" \
  upload --dataset ds008547 --affirmDefaced "$DATA" > "$LOG" 2>&1
status=$?

echo "upload exited ${status} - log: ${LOG}"
echo "failed transfers: $(grep -c 'Failed to transfer annex object' "$LOG" || true)"

# Preserve the git directory so a failed push can be retried with system git in
# minutes instead of re-hashing 226 GB. /tmp is node-local and wiped at job end.
R=$(ls -d /tmp/openneuro_cli_*/ds008547 2>/dev/null | head -1)
if [ -n "$R" ] && [ -d "$R/.git" ]; then
  rm -rf "$KEEP" && mkdir -p "$KEEP"
  cp -a "$R/.git" "$KEEP/ds008547.git" && echo "preserved git dir -> $KEEP/ds008547.git ($(du -sh "$KEEP/ds008547.git" | cut -f1))"
else
  echo "WARNING: could not locate repo to preserve"
fi

exit ${status}
