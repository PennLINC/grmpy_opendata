#!/bin/bash
#SBATCH -J qsirecon-upload
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 7-00:00:00
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/slurm_%j.log

set -eo pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
export OPENNEURO_LOG=INFO

CLI=/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched
DATA=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/qsirecon
LOG=/ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload_${SLURM_JOB_ID}.log

# Write the CLI's output straight to a regular file. Under SLURM, #SBATCH -o
# makes stdout a pipe to slurmstepd; Deno sets stdio pipes non-blocking, so a
# burst of log lines can fill the pipe and kill the job with
# "WouldBlock: Resource temporarily unavailable (os error 11)".
# O_NONBLOCK has no effect on regular files, so this cannot happen here.
deno run --allow-all --config "$CLI/deno.json" "$CLI/mod.ts" \
  upload --dataset ds008545 --affirmDefaced "$DATA" > "$LOG" 2>&1

echo "upload exited $? - log: $LOG"
grep -c "Failed to transfer annex object" "$LOG" | sed 's/^/failed transfers: /'