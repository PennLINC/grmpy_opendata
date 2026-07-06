#!/usr/bin/env python3
"""
Process the PRIME Screen-Revised export into a released TSV (plus JSON sidecar).

Pipeline
--------
1. The original item column names (``sip003`` .. ``sip026``) are retained.
   Scoring treats them positionally, as if ``sip003 = prime_1``,
   ``sip004 = prime_2``, and so on -- so the first 12 items (``sip003`` ..
   ``sip014``) drive the scoring. Administrative columns
   (``no_primescreen___*``, ``prime_screen_complete``, ``protocol_number``) are
   dropped; only ``participant_id`` and the items are kept.
2. ``prime_total_score`` is appended: the sum of the first 12 items (``sip003``
   .. ``sip014``). It is ``n/a`` unless all twelve items are present.
3. ``prime_clinical_significance`` is appended, flagged ``1`` when a
   participant meets ANY of three criteria based on the first 12 items:
     - >= 1 item rated 6 ("definitely agree"), OR
     - >= 3 items rated 5 ("somewhat agree"), OR
     - ``prime_total_score`` exceeds an age-specific cutoff.
   Every study participant is older than 11, so no lower age bound is applied;
   participants older than 21 use the age-21 cutoff. A participant who meets
   none of the criteria is ``0``; the flag is ``n/a`` only when the 12 scored
   items are incomplete.
4. All empty entries become ``n/a`` (BIDS convention).

Participant ages are loaded from the CuBIDS curation ``participants_tmp.tsv``.

The per-question ``Description`` / ``Levels`` metadata in ``ITEM_METADATA`` is
intentionally left blank to be filled in manually here; it is written verbatim
to the JSON sidecar on each run.

Example
-------
    python phenotype/09_process_prime.py \
        --input phenotype/data/prime_screen.tsv \
        --participants curation/04_cubids_curation/participants_tmp.tsv \
        --output-dir phenotype/data
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

PARTICIPANT_ID_COL = "participant_id"
NA = "n/a"
TERM_URL = {
    "https://doi.org/10.1016/j.schres.2008.08.018",
    "https://doi.org/10.1093/schbul/sbae224",
}

# Values treated as "no data".
_EMPTY_VALUES = {"", "n/a", "na", ".", "null", "none"}

# Number of PRIME items and which of them are used for scoring.
N_ITEMS = 24  # sip003 .. sip026
N_SCORED_ITEMS = 12  # the first 12 items (sip003 .. sip014) drive the scoring

# Original item column names, retained in the output. Scoring treats them
# positionally: sip003 == prime_1, sip004 == prime_2, and so on.
ITEM_COLUMNS: List[str] = [f"sip{i:03d}" for i in range(3, 3 + N_ITEMS)]
SCORED_COLUMNS: List[str] = ITEM_COLUMNS[:N_SCORED_ITEMS]

# prime_total_score cutoffs by integer age. Every participant is older than 11
# (so no lower bound is enforced) and anyone older than 21 uses the age-21
# cutoff. A participant is flagged clinically significant if their total score
# is strictly greater than the cutoff for their (clamped) age.
AGE_CUTOFFS: Dict[int, int] = {
    11: 36,
    12: 34,
    13: 32,
    14: 29,
    15: 28,
    16: 27,
    17: 27,
    18: 28,
    19: 23,
    20: 26,
    21: 23,
}

INSTRUCTIONS_003_014 = "The following questions ask about your personal experiences. We ask about your sensory, psychological, emotional, and social experiences. Some of these questions may seem to relate directly to your experiences and others may not. Based on your experiences within the past year, please tell me how much you agree or disagree with the following statements. Please listen carefully and tell me the answer that best describes your experiences."
INSTRUCTIONS_015_026 = "You said [insert statement]. How long has it been since you first had this thought or experience? Less than 1 month, between 1 month and 1 year, more than a year but not your whole life, your entire lifetime or as long as you can remember?"

# ---------------------------------------------------------------------------
# Per-question metadata for the JSON sidecar. Fill in "Description" and
# "Levels" for each item manually below; these are written to the JSON as-is.
# ---------------------------------------------------------------------------
ITEM_METADATA: "OrderedDict[str, dict]" = OrderedDict(
    [
        ("sip003", {
            "Description": "I think that I have felt that there are odd or unusual things going on that I can't explain.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip004", {
            "Description": "I think that I might be able to predict the future.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip005", {
            "Description": "I may have felt that there could possibly by something interrupting or controlling my thoughts, feelings, or actions.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip006", {
            "Description": "I have had the experience of doing somethign differently because of my superstitions.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip007", {
            "Description": "I think that I may get confused at times whether something I experience or percieve may be real or may be just part of my imagination or dreams.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip008", {
            "Description": "I have thought that it might be possible that other people can read my mind, or that I can read others' minds.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip009", {
            "Description": "I wonder if people may be planning ot hurt me or even may be about to hurt me.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip010", {
            "Description": "I believe that I have special natural or supernatural gifts beyond my talents and natural strengths.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip011", {
            "Description": "I think I might feel like my mind is \"playing tricks\" on me.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip012", {
            "Description": "I have had the experience of hearing faint or clear sounds of people or a person mumbling or talking when there is no one near me.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip013", {
            "Description": "I think that I may hear my own thoughts being said out loud.",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip014", {
            "Description": "I have benn concerned that I might be \"going crazy\".",
            "Levels": {
                "6": "Definitely agree",
                "5": "Somewhat agree",
                "4": "Slightly agree",
                "3": "Not sure",
                "2": "Slightly disagree",
                "1": "Somewhat disagree",
                "0": "Definitely disagree",
                }
            }),
        ("sip015", {
            "Description": "I think that I have felt that there are odd or unusual things going on that I can't explain.",
            "Levels": {
                "1": "Less than 1 month",
                "2": "Between 1 month and 1 year",
                "3": "More than a year but not your whole life",
                "4": "Your entire lifetime or as long as you can remember",
                "9": "Unknown"
                }
            }),
        ("sip016", {
            "Description": "I think that I might be able to predict the future.",
            "Levels": {
                "1": "Less than 1 month",
                "2": "Between 1 month and 1 year",
                "3": "More than a year but not your whole life",
                "4": "Your entire lifetime or as long as you can remember",
                "9": "Unknown"
                }
        ("sip017", {
            "Description": "", "Levels": {}}),
        ("sip018", {"Description": "", "Levels": {}}),
        ("sip019", {"Description": "", "Levels": {}}),
        ("sip020", {"Description": "", "Levels": {}}),
        ("sip021", {"Description": "", "Levels": {}}),
        ("sip022", {"Description": "", "Levels": {}}),
        ("sip023", {"Description": "", "Levels": {}}),
        ("sip024", {"Description": "", "Levels": {}}),
        ("sip025", {"Description": "", "Levels": {}}),
        ("sip026", {"Description": "", "Levels": {}}),
    ]
)

TOTAL_SCORE_METADATA = {
    "Description": (
        "Sum of the first 12 PRIME Screen-Revised items (sip003 through "
        "sip014). 'n/a' if any of those 12 items is missing."
    )
}

CLINICAL_SIGNIFICANCE_METADATA = {
    "Description": (
        "Clinical significance based on the first 12 items (sip003-sip014). "
        "'1' if the participant meets any of: (a) >= 1 item rated 6, "
        "(b) >= 3 items rated 5, or (c) prime_total_score above the "
        "age-specific cutoff (participants older than 21 use the age-21 "
        "cutoff). '0' if the participant meets none of the criteria. 'n/a' if "
        "the 12 scored items are incomplete."
    ),
    "Levels": {
        "1": "Meets at least one clinical significance criterion.",
        "0": "Meets no criterion.",
        "n/a": "Not evaluable (the 12 scored items are incomplete).",
    },
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/prime_screen.tsv"),
        help="Path to raw PRIME screen TSV (default: phenotype/data/prime_screen.tsv)",
    )
    parser.add_argument(
        "--participants",
        type=Path,
        default=Path("curation/04_cubids_curation/participants_tmp.tsv"),
        help="Path to participants_tmp.tsv (used to look up participant age).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data"),
        help="Directory to write prime.tsv and prime.json (default: phenotype/data)",
    )
    return parser.parse_args(list(argv))


def is_empty(value: Optional[str]) -> bool:
    return value is None or value.strip().lower() in _EMPTY_VALUES


def parse_rating(value: Optional[str]) -> Optional[int]:
    """Parse a raw item value (e.g. '4.0') into an integer rating, or None."""
    if is_empty(value):
        return None
    try:
        return int(round(float(value.strip())))
    except (TypeError, ValueError):
        return None


def load_ages(path: Path) -> Dict[str, int]:
    """Return ``{participant_id: integer_age}`` from participants_tmp.tsv.

    Ages are floored to whole years; unparseable/empty ages are omitted.
    """
    ages: Dict[str, int] = {}
    if not path.exists():
        return ages
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pid = (row.get(PARTICIPANT_ID_COL) or "").strip()
            raw_age = row.get("age")
            if not pid or is_empty(raw_age):
                continue
            try:
                ages[pid] = int(math.floor(float(raw_age.strip())))
            except (TypeError, ValueError):
                continue
    return ages


def age_cutoff(age: Optional[int]) -> Optional[int]:
    """Return the total-score cutoff for a participant's age, or None.

    Ages are clamped to the table's range: every participant is older than 11,
    and anyone older than 21 uses the age-21 cutoff.
    """
    if age is None:
        return None
    clamped = min(max(age, min(AGE_CUTOFFS)), max(AGE_CUTOFFS))
    return AGE_CUTOFFS[clamped]


def clinical_significance(
    scored_items: List[Optional[int]],
    total: Optional[int],
    age: Optional[int],
) -> str:
    """Compute the prime_clinical_significance value for one participant."""
    # Cannot score without a complete set of the first 12 items.
    if total is None:
        return NA

    n_rated_6 = sum(1 for v in scored_items if v == 6)
    n_rated_5 = sum(1 for v in scored_items if v == 5)
    if n_rated_6 >= 1 or n_rated_5 >= 3:
        return "1"

    cutoff = age_cutoff(age)
    if cutoff is not None:
        return "1" if total > cutoff else "0"

    return NA


def process_row(row: Dict[str, str], ages: Dict[str, int]) -> List[str]:
    """Build the output row: participant_id, items, total, significance."""
    pid = (row.get(PARTICIPANT_ID_COL) or "").strip() or NA

    ratings: List[Optional[int]] = [parse_rating(row.get(col)) for col in ITEM_COLUMNS]
    scored_items = ratings[:N_SCORED_ITEMS]

    if all(v is not None for v in scored_items):
        total: Optional[int] = sum(v for v in scored_items if v is not None)
    else:
        total = None

    age = ages.get(pid)
    significance = clinical_significance(scored_items, total, age)

    out: List[str] = [pid]
    out.extend(str(v) if v is not None else NA for v in ratings)
    out.append(str(total) if total is not None else NA)
    out.append(significance)
    return out


def write_tsv(rows: List[List[str]], output_dir: Path) -> Path:
    header = (
        [PARTICIPANT_ID_COL]
        + list(ITEM_COLUMNS)
        + ["prime_total_score", "prime_clinical_significance"]
    )
    path = output_dir / "prime.tsv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def write_json(output_dir: Path) -> Path:
    sidecar: "OrderedDict[str, object]" = OrderedDict()
    sidecar["MeasurementToolMetadata"] = OrderedDict(
        [
            ("Description", "PRIME Screen-Revised"),
            ("Instructions", INSTRUCTIONS),
            ("TermURL", TERM_URL),
        ]
    )
    sidecar[PARTICIPANT_ID_COL] = {"Description": "Participant ID Number"}
    for item, meta in ITEM_METADATA.items():
        sidecar[item] = meta
    sidecar["prime_total_score"] = TOTAL_SCORE_METADATA
    sidecar["prime_clinical_significance"] = CLINICAL_SIGNIFICANCE_METADATA

    path = output_dir / "prime.json"
    with path.open("w") as f:
        json.dump(sidecar, f, indent=2)
        f.write("\n")
    return path


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input TSV not found: {args.input}", file=sys.stderr)
        return 2

    ages = load_ages(args.participants)
    if not ages:
        print(
            f"[!] No ages loaded from {args.participants}; the age-based "
            "criterion cannot be evaluated for any participant.",
            file=sys.stderr,
        )

    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = reader.fieldnames or []
        rows = list(reader)

    if PARTICIPANT_ID_COL not in columns:
        print(
            f"Input is missing required '{PARTICIPANT_ID_COL}' column.", file=sys.stderr
        )
        return 2

    missing_items = [c for c in ITEM_COLUMNS if c not in columns]
    if missing_items:
        print(
            f"[!] Input is missing expected item columns: {', '.join(missing_items)}",
            file=sys.stderr,
        )

    out_rows = [process_row(row, ages) for row in rows]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = write_tsv(out_rows, args.output_dir)
    json_path = write_json(args.output_dir)

    n_sig = sum(1 for r in out_rows if r[-1] == "1")
    n_na = sum(1 for r in out_rows if r[-1] == NA)
    print(
        f"Wrote {tsv_path} ({N_ITEMS} items + 2 score columns, {len(out_rows)} rows).\n"
        f"Wrote {json_path}.\n"
        f"prime_clinical_significance: {n_sig} significant (1), "
        f"{len(out_rows) - n_sig - n_na} not (0), {n_na} n/a."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
