#!/bin/bash
#SBATCH -J qsirecon-upload1
#SBATCH -p genoa-std-mem
#SBATCH -c 2
#SBATCH -t 10-00:00:00
#SBATCH -o /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload_%j.log

set -eo pipefail

command -v micromamba >/dev/null || { echo "micromamba not on PATH - replace the two lines below with however you normally activate"; exit 1; }
eval "$(micromamba shell hook -s bash)"
micromamba activate openneuro
command -v openneuro >/dev/null || { echo "openneuro not on PATH - check the activation lines"; exit 1; }

export OPENNEURO_LOG=DEBUG
cd /ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/qsirecon
openneuro upload --new --verbose --affirmDefaced . < /dev/null
