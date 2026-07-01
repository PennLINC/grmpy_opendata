#!/usr/bin/env python3
"""
Collide participants_tmp.tsv/json into the BIDS participants.tsv/json.

Merges on participant_id (left join onto the existing participants.tsv so no
subjects are added or dropped) and inserts the tmp columns immediately after
participant_id, i.e. before the fracback score columns. The JSON sidecar keys
are reordered to match.

Run on CUBIC, e.g.:
    python collide_participants_tmp.py \
        --bids-root /cbica/projects/grmpy/data/bids_datalad \
        --tmp-dir .
"""

import argparse
import json
from pathlib import Path

import pandas as pd

NA = "n/a"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--bids-root",
        type=Path,
        default=Path("/cbica/projects/grmpy/data/bids_datalad"),
        help="BIDS root containing participants.tsv/json.",
    )
    p.add_argument(
        "--tmp-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory holding participants_tmp.tsv/json.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    participants_tsv = args.bids_root / "participants.tsv"
    participants_json = args.bids_root / "participants.json"
    tmp_tsv = args.tmp_dir / "participants_tmp.tsv"
    tmp_json = args.tmp_dir / "participants_tmp.json"

    part = pd.read_csv(participants_tsv, sep="\t", dtype=str)
    tmp = pd.read_csv(tmp_tsv, sep="\t", dtype=str)

    tmp_cols = [c for c in tmp.columns if c != "participant_id"]
    fracback_cols = [c for c in part.columns if c != "participant_id"]

    # Drop any pre-existing tmp columns so re-runs are idempotent.
    part = part.drop(columns=[c for c in tmp_cols if c in part.columns])
    fracback_cols = [c for c in fracback_cols if c not in tmp_cols]

    merged = part.merge(tmp, on="participant_id", how="left")
    merged = merged[["participant_id"] + tmp_cols + fracback_cols]
    merged.to_csv(participants_tsv, sep="\t", index=False, na_rep=NA)
    print(f"Updated {participants_tsv}: +{len(tmp_cols)} columns before fracback scores.")

    # ---- JSON sidecar ----
    with open(tmp_json) as f:
        tmp_side = json.load(f)
    side = {}
    if participants_json.exists():
        with open(participants_json) as f:
            side = json.load(f)

    ordered = {}
    if "participant_id" in side:
        ordered["participant_id"] = side["participant_id"]
    for col in tmp_cols:
        ordered[col] = tmp_side.get(col, {"Description": ""})
    for key, val in side.items():
        if key not in ordered:
            ordered[key] = val

    with open(participants_json, "w") as f:
        json.dump(ordered, f, indent=2)
        f.write("\n")
    print(f"Updated {participants_json}.")


if __name__ == "__main__":
    main()
