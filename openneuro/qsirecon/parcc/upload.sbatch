#!/bin/bash
#SBATCH -J qsirecon-upload2
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 7-00:00:00
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload_%j.log

set -eo pipefail
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro

export DENO_DIR=/tmp/deno-$USER && mkdir -p "$DENO_DIR"
export OPENNEURO_LOG=DEBUG

SRC=/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/qsirecon
STAGE=/tmp/qsirecon_stage

df -h /tmp
mkdir -p "$STAGE"
rsync -a "$SRC"/ "$STAGE"/
df -h /tmp

cd "$STAGE"
openneuro upload --new --verbose --affirmDefaced .