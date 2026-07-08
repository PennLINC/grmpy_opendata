#!/usr/bin/env python3
"""Cast categorical (Levels) fields in phenotype TSVs to integer text.

For every ``*.tsv`` under the phenotype data tree that has a matching ``*.json``
sidecar, this rewrites the columns whose sidecar entry defines ``Levels`` so
that integral values are stored without a trailing ``.0`` (``1.0`` -> ``1``).

Only columns with a ``Levels`` definition are touched. Every other column --
including derivative summary/subscale scores that have no ``Levels`` -- is left
byte-for-byte identical.

Safety guarantees (a file is only written if ALL of these hold):
  * A cell is changed only when its value parses to a float that is exactly
    integral. Missing markers (``n/a``, empty) and non-numeric level codes
    (e.g. ``V``, ``none``) are left untouched.
  * For every changed cell, ``float(old) == float(new)`` -- the numeric meaning
    is provably unchanged.
  * Non-``Levels`` columns and unchanged cells are verified byte-identical.
  * Row and column counts are unchanged.
  * Per-file line endings (LF vs CRLF) and trailing-newline presence are
    preserved exactly.

Run with ``--dry-run`` (default is to apply) to preview without writing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Values that represent "no data" and must never be coerced to an integer.
MISSING_TOKENS = {"", "n/a", "na", "nan"}


def load_level_columns(json_path: Path) -> set[str]:
    """Return the set of field names in ``json_path`` that define ``Levels``."""
    with json_path.open(encoding="utf-8") as fh:
        meta = json.load(fh)
    return {
        key
        for key, val in meta.items()
        if isinstance(val, dict) and "Levels" in val
    }


def maybe_cast(value: str) -> tuple[str, bool]:
    """Return (new_value, changed) for a single cell.

    A value is converted only if it parses to an integral float. Anything else
    (missing markers, non-numeric level codes, non-integral numbers) is
    returned unchanged.
    """
    if value.strip().lower() in MISSING_TOKENS:
        return value, False
    try:
        num = float(value)
    except ValueError:
        return value, False
    if not num.is_integer():
        # A fractional value in a categorical field: leave it and let the
        # caller flag it, since converting would lose information.
        return value, False
    new_value = str(int(num))
    return new_value, new_value != value


def split_keep_ends(text: str) -> list[str]:
    """Split into lines keeping their (possibly heterogeneous) terminators."""
    return text.splitlines(keepends=True)


def line_body_and_end(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""


def process_file(tsv_path: Path, json_path: Path, apply: bool) -> dict:
    """Process one TSV/JSON pair. Returns a stats dict; raises on any anomaly."""
    level_cols = load_level_columns(json_path)
    result = {
        "tsv": tsv_path,
        "level_cols_in_json": len(level_cols),
        "level_cols_in_tsv": 0,
        "cells_changed": 0,
        "nonintegral": [],  # (column, value) that could not be safely cast
        "written": False,
    }
    if not level_cols:
        return result

    with tsv_path.open(encoding="utf-8", newline="") as fh:
        original = fh.read()
    lines = split_keep_ends(original)
    if not lines:
        return result

    header_body, _ = line_body_and_end(lines[0])
    header = header_body.split("\t")
    target_idx = [i for i, name in enumerate(header) if name in level_cols]
    result["level_cols_in_tsv"] = len(target_idx)
    if not target_idx:
        return result

    out_lines: list[str] = [lines[0]]
    changed = 0
    for line in lines[1:]:
        body, end = line_body_and_end(line)
        if body == "" and end == "":
            out_lines.append(line)
            continue
        fields = body.split("\t")
        if len(fields) != len(header):
            raise ValueError(
                f"{tsv_path}: row has {len(fields)} fields, "
                f"expected {len(header)} (header)"
            )
        for i in target_idx:
            old = fields[i]
            new, did_change = maybe_cast(old)
            if did_change:
                # Prove the numeric meaning is identical before accepting.
                if float(old) != float(new):
                    raise AssertionError(
                        f"{tsv_path}: value meaning changed "
                        f"{old!r} -> {new!r} in column {header[i]!r}"
                    )
                fields[i] = new
                changed += 1
            elif old.strip().lower() not in MISSING_TOKENS:
                try:
                    if not float(old).is_integer():
                        result["nonintegral"].append((header[i], old))
                except ValueError:
                    pass  # non-numeric level code (e.g. "V", "none"): fine
        out_lines.append("\t".join(fields) + end)

    result["cells_changed"] = changed

    new_text = "".join(out_lines)

    # Structural verification: same number of lines, same non-Levels content.
    verify_unchanged_except_levels(original, new_text, target_idx)

    if changed and apply:
        with tsv_path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
        result["written"] = True
    return result


def verify_unchanged_except_levels(
    original: str, new_text: str, target_idx: list[int]
) -> None:
    """Assert original and new differ ONLY within the target columns, and that
    every differing target cell is numerically equal."""
    orig_lines = split_keep_ends(original)
    new_lines = split_keep_ends(new_text)
    if len(orig_lines) != len(new_lines):
        raise AssertionError("line count changed during processing")
    target = set(target_idx)
    for ln, (o_line, n_line) in enumerate(zip(orig_lines, new_lines)):
        o_body, o_end = line_body_and_end(o_line)
        n_body, n_end = line_body_and_end(n_line)
        if o_end != n_end:
            raise AssertionError(f"line ending changed on line {ln}")
        if o_body == n_body:
            continue
        o_fields = o_body.split("\t")
        n_fields = n_body.split("\t")
        if len(o_fields) != len(n_fields):
            raise AssertionError(f"field count changed on line {ln}")
        for i, (of, nf) in enumerate(zip(o_fields, n_fields)):
            if of == nf:
                continue
            if ln == 0:
                raise AssertionError("header text changed")
            if i not in target:
                raise AssertionError(
                    f"non-Levels column {i} changed on line {ln}: {of!r}->{nf!r}"
                )
            if float(of) != float(nf):
                raise AssertionError(
                    f"numeric meaning changed on line {ln} col {i}: "
                    f"{of!r}->{nf!r}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parent / "data"
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_dir,
        help=f"Root to search for TSV/JSON pairs (default: {default_dir})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing any files.",
    )
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    if not data_dir.is_dir():
        print(f"error: {data_dir} is not a directory", file=sys.stderr)
        return 2

    apply = not args.dry_run
    tsvs = sorted(data_dir.rglob("*.tsv"))

    total_cells = 0
    files_changed = 0
    files_with_levels = 0
    nonintegral_hits: list[tuple[Path, str, str]] = []

    for tsv in tsvs:
        json_path = tsv.with_suffix(".json")
        if not json_path.exists():
            continue
        try:
            res = process_file(tsv, json_path, apply=apply)
        except (ValueError, AssertionError) as exc:
            print(f"SKIPPED (verification failed): {exc}", file=sys.stderr)
            continue
        if res["level_cols_in_tsv"]:
            files_with_levels += 1
        for col, val in res["nonintegral"]:
            nonintegral_hits.append((tsv, col, val))
        if res["cells_changed"]:
            files_changed += 1
            total_cells += res["cells_changed"]
            rel = tsv.relative_to(data_dir)
            status = "wrote" if res["written"] else "would change"
            print(
                f"{status:>13}: {rel}  "
                f"({res['cells_changed']} cells across "
                f"{res['level_cols_in_tsv']} Levels columns)"
            )

    print("\n" + "=" * 60)
    mode = "DRY RUN (no files written)" if args.dry_run else "APPLIED"
    print(f"Mode: {mode}")
    print(f"TSVs with Levels columns: {files_with_levels}")
    print(f"Files changed: {files_changed}")
    print(f"Total cells cast to int: {total_cells}")
    if nonintegral_hits:
        print(
            f"\nWARNING: {len(nonintegral_hits)} non-integral value(s) found in "
            "Levels columns (left unchanged):"
        )
        for tsv, col, val in nonintegral_hits[:20]:
            print(f"  {tsv.name}:{col} = {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
