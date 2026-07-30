#!/bin/bash
#SBATCH -J qsirecon-upload
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 7-00:00:00
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload_%j.log

set -eo pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
export OPENNEURO_LOG=INFO


deno run --allow-all --config /ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched/deno.json /ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched/mod.ts upload --new --affirmDefaced /ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/qsirecon