#!/usr/bin/env python3
"""Finalize phenotype TSVs for BIDS-validator-clean release.

This processes every ``*.tsv`` (with a matching ``*.json`` sidecar) that lives
under the phenotype data tree but *outside* the ``final/`` folder, applies a set
of cleaning transforms, and then copies the cleaned tsv/json pairs into
``final/`` (excluding ``swan`` and ``axis``, which are intentionally not part of
the released set).

Transforms, in order, per source file:
  1. Drop superseded columns: in ``mapssr`` the mis-named ``mapsr_*`` summary
     columns (single 's') are removed -- they are superseded by the correctly
     named ``mapssr_*`` summary columns.
  2. Integer casting: for every column whose sidecar defines integer-valued
     ``Levels``, integral values are stored without a trailing ``.0``
     (``1.0`` -> ``1``). Columns whose ``Levels`` keys are NOT plain integers
     (e.g. the zero-padded clock times in ``psqi``) are left for their
     dedicated transform.
  3. suq bad-session blanking: any subject with *at least one* ``suq`` response
     that does not match one of the options in that field's ``Levels`` has their
     ENTIRE suq record (every column except ``participant_id``) set to ``n/a``,
     on the assumption the session was administered/collected incorrectly.
  4. wolf_post_imaging missing -> n/a: empty cells become ``n/a``.
  5. biss_madrs: an out-of-range ``biss_31`` response is set to ``n/a`` and that
     participant's ``biss_mania`` subscale total is set to ``n/a``.
  6. psqi clock times: ``psqi_1`` and ``psqi_3`` are zero-padded to the 4-digit
     ``HHMM`` form used by their ``Levels`` (``130`` -> ``0130``, ``0`` ->
     ``0000``).

Safety: every cell change is logged with a reason. After processing, the script
reconstructs the expected output from the original file plus the logged changes
(and column drops) and asserts it matches what was written byte-for-byte, so no
unlogged mutation can slip through. Each logged change is additionally checked
against its transform's rule (e.g. integer casts must be numerically equal).
Per-file line endings and trailing newlines are preserved.

Use ``--dry-run`` to preview without writing or copying.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from copy import deepcopy
from pathlib import Path

# Values that represent "no data" and are never treated as real responses.
MISSING_TOKENS = {"", "n/a", "na", "nan"}

# Stems that are processed in place but NOT copied into final/.
COPY_EXCLUDE = {"swan", "axis"}


# --------------------------------------------------------------------------- #
# TSV parsing helpers (line-ending preserving)
# --------------------------------------------------------------------------- #
def line_end(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


class Table:
    """A parsed TSV that preserves its exact line terminator style."""

    def __init__(self, path: Path):
        with path.open(encoding="utf-8", newline="") as fh:
            raw = fh.read()
        lines = raw.splitlines(keepends=True)
        if not lines:
            raise ValueError(f"{path}: empty file")
        self.term = line_end(lines[0]) or "\n"
        self.trailing_newline = bool(line_end(lines[-1]))
        bodies = [ln[: len(ln) - len(line_end(ln))] for ln in lines]
        # Guard against unexpected blank lines that our row model can't preserve.
        for i, b in enumerate(bodies):
            if b == "":
                raise ValueError(f"{path}: unexpected blank line at line {i + 1}")
        self.header = bodies[0].split("\t")
        self.rows = [b.split("\t") for b in bodies[1:]]
        for i, row in enumerate(self.rows):
            if len(row) != len(self.header):
                raise ValueError(
                    f"{path}: row {i + 2} has {len(row)} fields, "
                    f"expected {len(self.header)}"
                )

    def col_index(self, name: str) -> int:
        return self.header.index(name)

    def serialize(self) -> str:
        bodies = ["\t".join(self.header)] + ["\t".join(r) for r in self.rows]
        text = self.term.join(bodies)
        if self.trailing_newline:
            text += self.term
        return text


def load_levels(json_path: Path) -> dict[str, dict[str, str]]:
    """Return {field: Levels-dict} for fields that define Levels."""
    with json_path.open(encoding="utf-8") as fh:
        meta = json.load(fh)
    return {
        k: v["Levels"]
        for k, v in meta.items()
        if isinstance(v, dict) and "Levels" in v
    }


def is_plain_int(s: str) -> bool:
    s = s.strip()
    try:
        return str(int(s)) == s
    except ValueError:
        return False


def levels_are_integer_typed(level_keys) -> bool:
    """True if all *real* (non-missing) level keys are plain integers."""
    real = [k for k in level_keys if k.strip().lower() not in MISSING_TOKENS]
    return bool(real) and all(is_plain_int(k) for k in real)


def normalize_numeric(value: str) -> str:
    """Return the integer-string form of an integral numeric value, else the
    value unchanged (used only for comparing against integer Levels)."""
    try:
        fv = float(value)
    except ValueError:
        return value
    return str(int(fv)) if fv.is_integer() else value


# --------------------------------------------------------------------------- #
# Transforms. Each appends (row_idx, col_name, old, new, reason) to `changes`
# and returns nothing; column drops are handled separately.
# --------------------------------------------------------------------------- #
def transform_int_cast(table: Table, levels, changes, nonintegral):
    int_cols = {
        name
        for name, lv in levels.items()
        if levels_are_integer_typed(lv.keys())
    }
    idxs = [(i, n) for i, n in enumerate(table.header) if n in int_cols]
    for r, row in enumerate(table.rows):
        for i, name in idxs:
            old = row[i]
            if old.strip().lower() in MISSING_TOKENS:
                continue
            try:
                fv = float(old)
            except ValueError:
                continue  # non-numeric level code (e.g. "V"): leave for OOB pass
            if not fv.is_integer():
                nonintegral.append((name, old))
                continue
            new = str(int(fv))
            if new != old:
                row[i] = new
                changes.append((r, name, old, new, "cast"))


def transform_suq_subject_na(table: Table, levels, changes, **_):
    """Blank the full suq record of any subject with >=1 out-of-bounds response."""
    pid_idx = (
        table.col_index("participant_id")
        if "participant_id" in table.header
        else None
    )
    bad_rows: set[int] = set()
    for i, name in enumerate(table.header):
        lv = levels.get(name)
        if not lv:
            continue
        keys = set(lv.keys())
        for r, row in enumerate(table.rows):
            v = row[i]
            if v.strip().lower() in MISSING_TOKENS:
                continue
            if normalize_numeric(v) not in keys:
                bad_rows.add(r)
    for r in sorted(bad_rows):
        for i in range(len(table.header)):
            if i == pid_idx:
                continue
            old = table.rows[r][i]
            if old == "n/a":
                continue
            table.rows[r][i] = "n/a"
            changes.append((r, table.header[i], old, "n/a", "suq-subject-na"))


def transform_wolf_missing(table: Table, levels, changes, **_):
    for i, name in enumerate(table.header):
        if name == "participant_id":
            continue
        for r, row in enumerate(table.rows):
            if row[i] == "":
                row[i] = "n/a"
                changes.append((r, name, "", "n/a", "wolf-missing"))


def transform_biss(table: Table, levels, changes, **_):
    if "biss_31" not in table.header:
        return
    i31 = table.col_index("biss_31")
    keys = set(levels.get("biss_31", {}).keys())
    imania = table.col_index("biss_mania") if "biss_mania" in table.header else None
    for r, row in enumerate(table.rows):
        old = row[i31]
        if old.strip().lower() in MISSING_TOKENS:
            continue
        if normalize_numeric(old) not in keys:
            row[i31] = "n/a"
            changes.append((r, "biss_31", old, "n/a", "biss31-oob"))
            if imania is not None and row[imania] != "n/a":
                mania_old = row[imania]
                row[imania] = "n/a"
                changes.append((r, "biss_mania", mania_old, "n/a", "biss-mania"))


def transform_psqi_times(table: Table, levels, changes, nonintegral):
    for name in ("psqi_1", "psqi_3"):
        if name not in table.header:
            continue
        i = table.col_index(name)
        keys = set(levels.get(name, {}).keys())
        for r, row in enumerate(table.rows):
            old = row[i]
            if old.strip().lower() in MISSING_TOKENS:
                continue
            try:
                padded = str(int(float(old))).zfill(4)
            except ValueError:
                nonintegral.append((name, old))
                continue
            if keys and padded not in keys:
                nonintegral.append((name, f"{old}->{padded} (not a Level)"))
            if padded != old:
                row[i] = padded
                changes.append((r, name, old, padded, "psqi-pad"))


# Per-stem extra transforms (int-cast always runs first for every file).
FILE_TRANSFORMS = {
    "suq": [transform_suq_subject_na],
    "wolf_post_imaging": [transform_wolf_missing],
    "biss_madrs": [transform_biss],
    "psqi": [transform_psqi_times],
}

# Columns to drop, by stem. A predicate over column name.
DROP_COLUMNS = {
    "mapssr": lambda name: name.startswith("mapsr_"),  # not "mapssr_"
}


# --------------------------------------------------------------------------- #
# Verification
# --------------------------------------------------------------------------- #
def verify(original: Table, final: Table, dropped: list[str], changes) -> None:
    """Reconstruct expected output from `original` + logged edits + drops and
    assert it equals `final`. Also validate each change against its rule."""
    exp_header = [h for h in original.header if h not in dropped]
    keep_idx = [i for i, h in enumerate(original.header) if h not in dropped]
    exp_rows = [[row[i] for i in keep_idx] for row in original.rows]

    col_pos = {name: p for p, name in enumerate(exp_header)}
    for r, name, old, new, reason in changes:
        if name not in col_pos:
            raise AssertionError(f"change targets missing/dropped column {name!r}")
        c = col_pos[name]
        if exp_rows[r][c] != old:
            raise AssertionError(
                f"stale change for {name!r} row {r}: expected old {old!r}, "
                f"found {exp_rows[r][c]!r}"
            )
        _validate_rule(reason, old, new)
        exp_rows[r][c] = new

    if exp_header != final.header:
        raise AssertionError("header mismatch after reconstruction")
    if exp_rows != final.rows:
        raise AssertionError("row content mismatch after reconstruction")


def _validate_rule(reason: str, old: str, new: str) -> None:
    if reason == "cast":
        if float(old) != float(new) or not is_plain_int(new):
            raise AssertionError(f"bad int cast {old!r}->{new!r}")
    elif reason in ("suq-subject-na", "biss31-oob", "biss-mania", "wolf-missing"):
        if new != "n/a":
            raise AssertionError(f"{reason} must set n/a, got {new!r}")
        if reason == "wolf-missing" and old != "":
            raise AssertionError(f"wolf-missing old must be empty, got {old!r}")
    elif reason == "psqi-pad":
        if int(float(old)) != int(new) or len(new) != 4:
            raise AssertionError(f"bad psqi pad {old!r}->{new!r}")
    else:
        raise AssertionError(f"unknown change reason {reason!r}")


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def process_file(tsv: Path, json_path: Path):
    stem = tsv.stem
    original = Table(tsv)
    working = deepcopy(original)
    levels = load_levels(json_path)
    changes: list[tuple] = []
    nonintegral: list[tuple] = []

    dropped = [h for h in working.header if DROP_COLUMNS.get(stem, lambda n: False)(h)]
    if dropped:
        keep = [i for i, h in enumerate(working.header) if h not in dropped]
        working.header = [working.header[i] for i in keep]
        working.rows = [[row[i] for i in keep] for row in working.rows]

    transform_int_cast(working, levels, changes, nonintegral)
    for fn in FILE_TRANSFORMS.get(stem, []):
        fn(working, levels, changes, nonintegral=nonintegral)

    verify(original, working, dropped, changes)
    return working, dropped, changes, nonintegral


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_dir = Path(__file__).resolve().parent / "data"
    parser.add_argument("--data-dir", type=Path, default=default_dir)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_dir: Path = args.data_dir
    final_dir = data_dir / "final"
    apply = not args.dry_run
    if not data_dir.is_dir():
        print(f"error: {data_dir} is not a directory", file=sys.stderr)
        return 2

    sources = []
    for tsv in sorted(data_dir.rglob("*.tsv")):
        rel = tsv.relative_to(data_dir)
        if "final" in rel.parts:
            continue
        json_path = tsv.with_suffix(".json")
        if json_path.exists():
            sources.append((tsv, json_path))

    total_changes = 0
    copied = 0
    all_nonintegral: list[tuple] = []

    for tsv, json_path in sources:
        try:
            working, dropped, changes, nonintegral = process_file(tsv, json_path)
        except (ValueError, AssertionError) as exc:
            print(f"SKIPPED (verification failed): {tsv.name}: {exc}", file=sys.stderr)
            continue

        rel = tsv.relative_to(data_dir)
        if changes or dropped:
            reasons = {}
            for *_, reason in changes:
                reasons[reason] = reasons.get(reason, 0) + 1
            summary = ", ".join(f"{k}:{v}" for k, v in sorted(reasons.items()))
            drop_note = f" drop_cols:{len(dropped)}" if dropped else ""
            action = "wrote" if apply else "would change"
            print(f"{action:>13}: {rel}  [{summary}{drop_note}]")
            total_changes += len(changes)

        if apply and (changes or dropped):
            with tsv.open("w", encoding="utf-8", newline="") as fh:
                fh.write(working.serialize())
            # confirm on-disk content matches what we verified
            if Table(tsv).serialize() != working.serialize():
                raise SystemExit(f"post-write mismatch: {tsv}")

        for item in nonintegral:
            all_nonintegral.append((tsv.name, *item))

    # Copy cleaned pairs into final/ (excluding swan & axis).
    if apply:
        final_dir.mkdir(exist_ok=True)
    for tsv, json_path in sources:
        if tsv.stem in COPY_EXCLUDE:
            continue
        if apply:
            for src in (tsv, json_path):
                dst = final_dir / src.name
                shutil.copy2(src, dst)
                if dst.read_bytes() != src.read_bytes():
                    raise SystemExit(f"copy mismatch: {dst}")
        copied += 1

    print("\n" + "=" * 64)
    print(f"Mode: {'APPLIED' if apply else 'DRY RUN (no writes/copies)'}")
    print(f"Source files processed: {len(sources)}")
    print(f"Total cell changes: {total_changes}")
    print(f"Pairs {'copied' if apply else 'to copy'} to final/: {copied} "
          f"(excluded: {', '.join(sorted(COPY_EXCLUDE))})")
    if all_nonintegral:
        print(f"\nWARNING: {len(all_nonintegral)} value(s) needed attention:")
        for name, col, val in all_nonintegral[:20]:
            print(f"  {name}:{col} = {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
