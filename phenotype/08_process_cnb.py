#!/usr/bin/env python3
"""
Split the raw Penn CNB export into one TSV (plus JSON sidecar) per CNB task.

Pipeline
--------
1. Every column in ``CNB_raw.tsv`` is parsed into a (task, metric) pair using an
   explicit, reviewable crosswalk (``TASK_PATTERNS``). The metric is the part of
   the raw column name that corresponds to an NDA ``penncnb01`` element suffix.
2. The candidate NDA element name ``cnb_<task>_<metric>`` is looked up in
   ``NDA_penncnb01_definitions.csv``. Columns whose candidate exists are
   "releasable"; everything else is routed to ``misc_cnb_raw.tsv`` for manual
   inspection (e.g. WRAT4, per-test ``valid_code`` columns, race / same-trial
   breakdowns, PCET WIS metrics, and administrative columns).
3. The Penn CNB administers alternate forms of several tasks (e.g. ADT36-A vs
   ADT36-B, ER40 C vs D). Each participant completed at most one form, so the
   per-form raw columns are *coalesced* into the single NDA element they share
   (first non-empty value wins; conflicting non-empty values are reported).
4. Output column names are the NDA element names. JSON sidecars carry the NDA
   ``ElementDescription`` for each column and a shared ``TermURL``.

The ``grmpy_data_dict.csv`` ``source`` / ``var_name`` / ``var_description``
columns are used to attach the original GRMPY description to each mapped column
in the audit report (``cnb_nda_mapping.tsv``), and to flag any released column
that is undocumented in the data dictionary.

Example
-------
    python phenotype/08_process_cnb.py \
        --input phenotype/data/CNB_raw.tsv \
        --nda-defs ignore/NDA_penncnb01_definitions.csv \
        --data-dict ignore/grmpy_data_dict.csv \
        --output-dir phenotype/data/cnb
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PARTICIPANT_ID_COL = "participant_id"
NA = "n/a"
TERM_URL = "https://nda.nih.gov/data-structure/penncnb01"

# Values that are treated as "no data" when coalescing alternate forms.
_EMPTY_VALUES = {"", "n/a", "na", ".", "null", "none"}

# Human-readable task names used in the JSON ``MeasurementToolMetadata``.
TASK_DESCRIPTIONS: Dict[str, str] = {
    "adt": "Penn Age Differentiation Test (ADT)",
    "cpf": "Penn Face Memory Test (CPF)",
    "er40": "Penn Emotion Recognition Test (ER40)",
    "gng": "Go/No-Go Test (GNG)",
    "cpw": "Penn Word Memory Test (CPW)",
    "pvrt": "Penn Verbal Reasoning Test (PVRT)",
    "medf": "Measured Emotion Differentiation Test (MEDF)",
    "mpract": "Motor Praxis Test (MPRACT)",
    "pcet": "Penn Conditional Exclusion Test (PCET)",
    "pmat": "Penn Matrix Reasoning Test (PMAT)",
    "ctap": "Computerized Finger Tapping Test (CTAP)",
    "lnb": "Letter N-Back Test (LNB)",
    "cptnl": "Penn Continuous Performance Test, Number-Letter (CPT-NL)",
    "volt": "Visual Object Learning Test (VOLT)",
    "plot": "Penn Line Orientation Test (PLOT)",
}

# SPCPTNL raw columns encode the condition as scpl/scpn/scpt; NDA spells these
# out as letter/number/total.
_CPTNL_CONDITIONS = {"scpl": "letter", "scpn": "number", "scpt": "total"}

# NDA elements that resolve via the crosswalk but should NOT be released; any raw
# column mapping to one of these is routed to misc_cnb_raw.tsv instead.
EXCLUDE_NDA_ELEMENTS = {
    "cnb_pvrt_form",
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/CNB_raw.tsv"),
        help="Path to raw Penn CNB TSV (default: phenotype/data/CNB_raw.tsv)",
    )
    parser.add_argument(
        "--nda-defs",
        type=Path,
        default=Path("ignore/NDA_penncnb01_definitions.csv"),
        help="Path to NDA penncnb01 element definitions CSV.",
    )
    parser.add_argument(
        "--data-dict",
        type=Path,
        default=Path("ignore/grmpy_data_dict.csv"),
        help="Path to GRMPY data dictionary CSV (source/var_name/var_description).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data/cnb"),
        help="Directory for per-task TSV/JSON, misc, and mapping report.",
    )
    return parser.parse_args(list(argv))


def extract_task_metric(column: str) -> Tuple[Optional[str], Optional[str]]:
    """Map a raw CNB column name to an (nda_task, metric) pair.

    ``metric`` is the suffix that, combined with the task, forms a candidate NDA
    element ``cnb_<task>_<metric>``. Returns ``(None, None)`` for columns that do
    not belong to a recognised task (administrative columns, valid codes, etc.).
    """
    # SPCPTNL needs the condition token rewritten before the metric.
    m = re.match(r"^spcptnl_(scp[lnt])_(.+)$", column)
    if m:
        return "cptnl", f"{_CPTNL_CONDITIONS[m.group(1)]}_{m.group(2)}"

    # (task, regex) where group(1) is the NDA metric suffix. The leading,
    # often-duplicated, test/form token is stripped so only the metric remains.
    patterns: List[Tuple[str, str]] = [
        ("adt", r"^adt36_[ab]_adt36[ab]_(.+)$"),
        ("cpf", r"^cpf_[ab]_cpf_(.+)$"),
        # Form A is named er40_a_er40_* (no inner form letter); C/D are
        # er40_c_er40c_* / er40_d_er40d_* -- so the inner letter is optional.
        ("er40", r"^er40_[acd]_er40[acd]?_(.+)$"),
        ("gng", r"^gng150_gng150_(.+)$"),
        ("cpw", r"^kcpw_a_cpw_(.+)$"),
        ("pvrt", r"^kspvrt_[abd]_kspvrt[abd]_(.+)$"),
        ("medf", r"^medf36_[ab]_medf36[ab]_(.+)$"),
        ("mpract", r"^mpract_(mp.+)$"),
        ("pcet", r"^s?pcet_[ab]_s?pcet_(.+)$"),
        ("pmat", r"^pmat24_[ab]_pmat24_[ab]_(.+)$"),
        ("ctap", r"^sctap_sctap_(.+)$"),
        ("lnb", r"^slnb2_90_slnb2_(.+)$"),
        ("volt", r"^svolt_a_svolt_(.+)$"),
        ("plot", r"^vsplot(?:15|24)_vsplot(?:15|24)_(.+)$"),
    ]
    for task, pattern in patterns:
        m = re.match(pattern, column)
        if m:
            return task, m.group(1)
    return None, None


def load_nda_defs(path: Path) -> "OrderedDict[str, str]":
    """Return ordered ``{ElementName: ElementDescription}`` from the NDA CSV."""
    defs: "OrderedDict[str, str]" = OrderedDict()
    with path.open("r", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("ElementName") or "").strip()
            if name:
                defs[name] = (row.get("ElementDescription") or "").strip()
    return defs


def load_data_dict(path: Path) -> Dict[str, str]:
    """Return ``{lower(source_varname): var_description}`` from the data dict."""
    lookup: Dict[str, str] = {}
    if not path.exists():
        return lookup
    with path.open("r", newline="") as f:
        for row in csv.DictReader(f):
            source = (row.get("source") or "").strip()
            var_name = (row.get("var_name") or "").strip()
            if not source or not var_name:
                continue
            key = f"{source}_{var_name}".lower()
            lookup[key] = (row.get("var_description") or "").strip()
    return lookup


def is_empty(value: Optional[str]) -> bool:
    return value is None or value.strip().lower() in _EMPTY_VALUES


def coalesce(row: Dict[str, str], source_cols: List[str]) -> Tuple[str, bool]:
    """Return (value, conflict) by taking the first non-empty source value.

    ``conflict`` is True if more than one source column is non-empty with
    differing values (each participant should only have completed one form).
    """
    found: List[str] = [row[c].strip() for c in source_cols if not is_empty(row.get(c))]
    if not found:
        return NA, False
    conflict = len(set(found)) > 1
    return found[0], conflict


def build_task_mapping(
    columns: List[str], nda_defs: "OrderedDict[str, str]"
) -> Tuple[
    "OrderedDict[str, OrderedDict[str, List[str]]]", List[Tuple[str, str, str]], List[str]
]:
    """Resolve raw columns into per-task NDA-element mappings.

    Returns:
      task_map: task -> {nda_element: [raw_source_cols]} (NDA element order)
      mapping_rows: (raw_col, task, nda_element) for every released raw column
      misc_cols: raw columns not mapped to any NDA element (original order)
    """
    # task -> nda_element -> [raw cols]
    raw_map: Dict[str, "defaultdict[str, List[str]]"] = defaultdict(
        lambda: defaultdict(list)
    )
    mapping_rows: List[Tuple[str, str, str]] = []
    misc_cols: List[str] = []

    for col in columns:
        if col == PARTICIPANT_ID_COL:
            continue
        task, metric = extract_task_metric(col)
        nda_element = f"cnb_{task}_{metric}" if task else None
        if (
            nda_element
            and nda_element in nda_defs
            and nda_element not in EXCLUDE_NDA_ELEMENTS
        ):
            raw_map[task][nda_element].append(col)
            mapping_rows.append((col, task, nda_element))
        else:
            misc_cols.append(col)

    # Order tasks by first appearance and elements by NDA definition order.
    nda_order = {name: i for i, name in enumerate(nda_defs)}
    task_map: "OrderedDict[str, OrderedDict[str, List[str]]]" = OrderedDict()
    for task in TASK_DESCRIPTIONS:
        if task not in raw_map:
            continue
        ordered = OrderedDict(
            sorted(raw_map[task].items(), key=lambda kv: nda_order[kv[0]])
        )
        task_map[task] = ordered

    return task_map, mapping_rows, misc_cols


def write_task_outputs(
    task: str,
    element_map: "OrderedDict[str, List[str]]",
    rows: List[Dict[str, str]],
    nda_defs: "OrderedDict[str, str]",
    output_dir: Path,
) -> Tuple[int, int]:
    """Write ``cnb_<task>.tsv`` and ``cnb_<task>.json``. Returns (ncols, nconflicts)."""
    elements = list(element_map.keys())
    header = [PARTICIPANT_ID_COL] + elements

    tsv_path = output_dir / f"cnb_{task}.tsv"
    conflicts = 0
    with tsv_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            out = [row.get(PARTICIPANT_ID_COL, "") or NA]
            for element in elements:
                value, conflict = coalesce(row, element_map[element])
                conflicts += conflict
                out.append(value)
            writer.writerow(out)

    sidecar: "OrderedDict[str, object]" = OrderedDict()
    sidecar["MeasurementToolMetadata"] = OrderedDict(
        [
            ("Description", TASK_DESCRIPTIONS[task]),
            ("TermURL", TERM_URL),
        ]
    )
    sidecar[PARTICIPANT_ID_COL] = {"Description": "Participant ID Number"}
    for element in elements:
        sidecar[element] = {"Description": nda_defs[element] or element}
    json_path = output_dir / f"cnb_{task}.json"
    with json_path.open("w") as f:
        json.dump(sidecar, f, indent=2)
        f.write("\n")

    return len(elements), conflicts


def write_misc(misc_cols: List[str], rows: List[Dict[str, str]], output_dir: Path) -> None:
    header = [PARTICIPANT_ID_COL] + misc_cols
    path = output_dir / "misc_cnb_raw.tsv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            out = [row.get(PARTICIPANT_ID_COL, "") or NA]
            out.extend((row.get(c, "") or NA) for c in misc_cols)
            writer.writerow(out)


def write_mapping_report(
    mapping_rows: List[Tuple[str, str, str]],
    misc_cols: List[str],
    nda_defs: "OrderedDict[str, str]",
    data_dict: Dict[str, str],
    output_dir: Path,
) -> None:
    path = output_dir / "cnb_nda_mapping.tsv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "raw_column",
                "status",
                "task",
                "nda_element",
                "nda_description",
                "grmpy_description",
            ]
        )
        for raw_col, task, element in mapping_rows:
            writer.writerow(
                [
                    raw_col,
                    "released",
                    task,
                    element,
                    nda_defs.get(element, ""),
                    data_dict.get(raw_col, ""),
                ]
            )
        for raw_col in misc_cols:
            writer.writerow(
                [raw_col, "misc", "", "", "", data_dict.get(raw_col, "")]
            )


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    for required in (args.input, args.nda_defs):
        if not required.exists():
            print(f"Required input not found: {required}", file=sys.stderr)
            return 2

    nda_defs = load_nda_defs(args.nda_defs)
    data_dict = load_data_dict(args.data_dict)

    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = reader.fieldnames or []
        rows = list(reader)
    if PARTICIPANT_ID_COL not in columns:
        print(f"Input is missing required '{PARTICIPANT_ID_COL}' column.", file=sys.stderr)
        return 2

    task_map, mapping_rows, misc_cols = build_task_mapping(columns, nda_defs)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    total_cols = 0
    total_conflicts = 0
    for task, element_map in task_map.items():
        ncols, nconflicts = write_task_outputs(
            task, element_map, rows, nda_defs, args.output_dir
        )
        total_cols += ncols
        total_conflicts += nconflicts
        flag = f"  [!] {nconflicts} form conflicts" if nconflicts else ""
        print(f"  cnb_{task}.tsv: {ncols} columns{flag}")

    write_misc(misc_cols, rows, args.output_dir)
    write_mapping_report(mapping_rows, misc_cols, nda_defs, data_dict, args.output_dir)

    undocumented = [c for c, _, _ in mapping_rows if c not in data_dict]
    print(
        f"\nWrote {len(task_map)} tasks ({total_cols} NDA columns) and "
        f"misc_cnb_raw.tsv ({len(misc_cols)} columns) for {len(rows)} participants."
    )
    print(f"Output directory: {args.output_dir}")
    if total_conflicts:
        print(
            f"[!] {total_conflicts} cells had >1 non-empty alternate-form value "
            "(kept first; review cnb_nda_mapping.tsv).",
            file=sys.stderr,
        )
    if undocumented:
        print(
            f"[!] {len(undocumented)} released columns absent from the data "
            f"dictionary: {', '.join(undocumented[:10])}"
            + (" ..." if len(undocumented) > 10 else ""),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
