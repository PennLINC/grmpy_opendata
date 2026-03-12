#!/usr/bin/env python3
"""
Add summary scores to per-instrument TSVs produced by `03_separate_self_reports.py`,
following the logic in `GRMPY_selfReportScoringCode_v4.R` (skipping collateral versions).

Usage:
  python phenotype/04_score_self_reports.py \
    --input-dir phenotype/data \
    --output-dir phenotype/data

  # Process only one instrument:
  python phenotype/04_score_self_reports.py --file bdi.tsv

Notes:
- Operates per instrument file (e.g., `aces.tsv`, `bdi.tsv`, ...). If a file is
  missing required columns, that instrument is skipped gracefully.
- Existing columns are preserved; new summary-score columns are appended.
- For any row that was entirely empty prior to scoring (ignoring `participant_id`),
  any newly added summary-score columns are cleared to missing values.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional


try:
    import pandas as pd
except Exception as exc:  # pragma: no cover - import error path
    raise SystemExit(
        "pandas is required. Please install it (e.g., `pip install pandas`)."
    ) from exc


PARTICIPANT_ID_COL = "participant_id"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score per-instrument TSVs created by 03_separate_self_reports.py, "
            "adding summary score columns in-place or to an output directory."
        )
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("phenotype/data"),
        help=("Directory containing instrument TSVs (default: phenotype/data)"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Directory to write scored TSVs (default: same as --input-dir). "
            "Files are overwritten if output equals input."
        ),
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        metavar="FILENAME",
        help=(
            "Process only this TSV file (e.g. bdi.tsv). Looked up in --input-dir. "
            "If omitted, all *.tsv files in the input directory are processed."
        ),
    )
    return parser.parse_args(list(argv))


def _fill_empty_with_na(df: pd.DataFrame) -> pd.DataFrame:
    """Replace empty entries with 'n/a' (BIDS convention)."""
    for col in df.columns:
        s = df[col]
        if s.dtype == object:
            # Empty string, whitespace-only, or already NaN → treat as missing
            mask = s.isna() | s.astype(str).str.strip().eq("")
            df[col] = s.where(~mask, other="n/a")
    return df.fillna("n/a")


def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def sum_columns(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    existing = [c for c in columns if c in df.columns]
    if not existing:
        return pd.Series([math.nan] * len(df), index=df.index)
    return df[existing].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)


def sum_columns_complete(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    """Sum columns only where all columns have valid values (n/a/missing → NaN in total)."""
    existing = [c for c in columns if c in df.columns]
    if not existing or len(existing) != len(columns):
        return pd.Series([math.nan] * len(df), index=df.index)
    num = df[existing].apply(pd.to_numeric, errors="coerce")
    all_present = num.notna().all(axis=1)
    return num.sum(axis=1).where(all_present)


def sum_columns_complete_transform(
    df: pd.DataFrame,
    columns: List[str],
    transform: Callable[[pd.Series], pd.Series],
) -> pd.Series:
    """Sum of transform(col) only where all columns have valid values."""
    existing = [c for c in columns if c in df.columns]
    if not existing or len(existing) != len(columns):
        return pd.Series([math.nan] * len(df), index=df.index)
    num = df[existing].apply(pd.to_numeric, errors="coerce")
    all_present = num.notna().all(axis=1)
    transformed = pd.DataFrame({c: transform(df[c]) for c in existing})
    return transformed.sum(axis=1).where(all_present)


def mean_columns(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    existing = [c for c in columns if c in df.columns]
    if not existing:
        return pd.Series([math.nan] * len(df), index=df.index)
    return df[existing].apply(pd.to_numeric, errors="coerce").mean(axis=1)


def mean_columns_complete(df: pd.DataFrame, columns: List[str]) -> pd.Series:
    """Mean only where all columns have valid values (n/a/missing → NaN)."""
    existing = [c for c in columns if c in df.columns]
    if not existing or len(existing) != len(columns):
        return pd.Series([math.nan] * len(df), index=df.index)
    num = df[existing].apply(pd.to_numeric, errors="coerce")
    all_present = num.notna().all(axis=1)
    return num.mean(axis=1).where(all_present)


def reverse_1_to_4(series: pd.Series) -> pd.Series:
    # R code uses (4 - x) + 1 == 5 - x
    return 5 - to_numeric(series)


def reverse_0_to_1(series: pd.Series) -> pd.Series:
    # R code uses (1 - x) for binary-like items
    return 1 - to_numeric(series)


def add_als_scores(df: pd.DataFrame) -> pd.DataFrame:
    item_cols = [f"als_{i}" for i in range(1, 19)]
    df["als_score_avg"] = mean_columns_complete(df, item_cols)
    return df


def add_mapsr_scores(df: pd.DataFrame) -> pd.DataFrame:
    # Columns are prefixed with mapssr_
    item_cols = [f"mapssr_{i}" for i in range(1, 16)]
    df["mapsr_rawtot_sum"] = sum_columns_complete(df, item_cols)
    df["mapsr_social_sum"] = sum_columns_complete(
        df, ["mapssr_1", "mapssr_2", "mapssr_3"]
    )
    df["mapsr_recvoc_sum"] = sum_columns_complete(
        df, ["mapssr_4", "mapssr_5", "mapssr_6"]
    )
    df["mapsr_motrelation_sum"] = sum_columns_complete(
        df, ["mapssr_7", "mapssr_8", "mapssr_9"]
    )
    df["mapsr_engage_sum"] = sum_columns_complete(
        df,
        ["mapssr_10", "mapssr_11", "mapssr_12", "mapssr_13", "mapssr_14", "mapssr_15"],
    )
    return df


def add_swan_scores(df: pd.DataFrame) -> pd.DataFrame:
    part1 = [f"swan_{i}" for i in range(1, 10)]
    part2 = [f"swan_{i}" for i in range(10, 19)]
    df["swan_total1"] = sum_columns_complete(df, part1)
    df["swan_total2"] = sum_columns_complete(df, part2)

    # ADHD classification flags
    t1 = to_numeric(df["swan_total1"]) if "swan_total1" in df else pd.Series()
    t2 = to_numeric(df["swan_total2"]) if "swan_total2" in df else pd.Series()

    def flag(series_cond: pd.Series) -> pd.Series:
        return (
            series_cond.astype("float")
            .where(~series_cond.isna(), other=math.nan)
            .astype("Int64")
        )

    # Only classify when both subscale totals are present; otherwise leave NA
    valid = t1.notna() & t2.notna()
    cond_combined = (t1 >= 6) & (t2 >= 6)
    cond_inatt = (t1 >= 6) & (t2 < 6)
    cond_hyper = (t1 < 6) & (t2 >= 6)
    cond_none = (t1 < 6) & (t2 < 6)

    def flag_valid(series_cond: pd.Series) -> pd.Series:
        out = flag(series_cond)
        return out.where(valid, other=pd.NA)

    df["eswanADHD_score_combined"] = flag_valid(cond_combined)
    df["eswanADHD_score_inattentive"] = flag_valid(cond_inatt)
    df["eswanADHD_score_hyperactive"] = flag_valid(cond_hyper)
    df["eswanADHD_score_noADHD"] = flag_valid(cond_none)
    return df


def add_aces_scores(df: pd.DataFrame) -> pd.DataFrame:
    aces_items = [f"aces_{i}" for i in range(1, 11)]
    df["aces_score_total"] = sum_columns_complete(df, aces_items)
    return df


def add_scared_scores(df: pd.DataFrame) -> pd.DataFrame:
    item_cols = [f"scared_{i}" for i in range(1, 42)]
    total = sum_columns_complete(df, item_cols)
    df["scared_score_total"] = total
    df["scared_score_anxietyDisorder"] = (
        (to_numeric(total) >= 25)
        .astype("float")
        .where(~total.isna(), other=math.nan)
        .astype("Int64")
    )
    return df


def add_rpaq_scores(df: pd.DataFrame) -> pd.DataFrame:
    proactive = [2, 4, 6, 9, 10, 12, 15, 17, 18, 20, 21, 23]
    reactive = [1, 3, 5, 7, 8, 11, 13, 14, 16, 19, 22]
    df["rpaq_score_proactiveTotal"] = sum_columns_complete(
        df, [f"rpaq_{i}" for i in proactive]
    )
    df["rpaq_score_reactiveTotal"] = sum_columns_complete(
        df, [f"rpaq_{i}" for i in reactive]
    )
    return df


def add_ari_scores(df: pd.DataFrame) -> pd.DataFrame:
    items = [f"ari_{i}" for i in range(1, 7)]
    df["ari_score_avg"] = mean_columns_complete(df, items)
    df["ari_score_total"] = sum_columns_complete(df, items)
    return df


def add_bdi_scores(df: pd.DataFrame) -> pd.DataFrame:
    # Sum all BDI items 1–21 except bdi_19a (include bdi_19)
    expected = [f"bdi_{i}" for i in range(1, 22)]
    df["bdi_score_total"] = sum_columns_complete(df, expected)
    return df


def add_bisbas_scores(df: pd.DataFrame) -> pd.DataFrame:
    # BIS total: reverse code select items from 1..4 scale
    bis1_items = [8, 13, 16, 19, 24]  # reversed
    bis2_items = [2, 22]  # not reversed
    bis1_cols = [f"bisbas_{i}" for i in bis1_items]
    bis2_cols = [f"bisbas_{i}" for i in bis2_items]

    s1 = sum_columns_complete_transform(df, bis1_cols, reverse_1_to_4)
    s2 = sum_columns_complete(df, bis2_cols)
    df["bis_score_total"] = (s1 + s2).where(s1.notna() & s2.notna())

    # BAS subscales (reverse-coded)
    bas_drive = [3, 9, 12, 21]
    bas_fun = [5, 10, 15, 20]
    bas_reward = [4, 7, 14, 18, 23]

    df["bas_score_driveTotal"] = sum_columns_complete_transform(
        df, [f"bisbas_{i}" for i in bas_drive], reverse_1_to_4
    )
    df["bas_score_funTotal"] = sum_columns_complete_transform(
        df, [f"bisbas_{i}" for i in bas_fun], reverse_1_to_4
    )
    df["bas_score_rewardTotal"] = sum_columns_complete_transform(
        df, [f"bisbas_{i}" for i in bas_reward], reverse_1_to_4
    )
    return df


def add_grit_scores(df: pd.DataFrame) -> pd.DataFrame:
    grittiness = [2, 4, 5, 7, 8, 10]
    openness = [1, 3, 6, 9, 11, 12]
    df["grit_score_grittiness"] = mean_columns_complete(
        df, [f"grit_{i}" for i in grittiness]
    )
    df["grit_score_openness"] = mean_columns_complete(
        df, [f"grit_{i}" for i in openness]
    )
    return df


def add_hcl16_scores(df: pd.DataFrame) -> pd.DataFrame:
    # HCL-16 item columns: hcl16_3_1 through hcl16_3_16
    item_cols = [f"hcl16_3_{i}" for i in range(1, 17)]
    df["hcl_score_total"] = sum_columns_complete(df, item_cols)
    return df


def add_bss_scores(df: pd.DataFrame) -> pd.DataFrame:
    items = [f"bss_{i}" for i in range(1, 9)]
    df["bss_score_mean"] = mean_columns_complete(df, items)
    df["bss_score_experience"] = mean_columns_complete(df, ["bss_1", "bss_5"])
    df["bss_score_boredom"] = mean_columns_complete(df, ["bss_2", "bss_6"])
    df["bss_score_thrill"] = mean_columns_complete(df, ["bss_3", "bss_7"])
    df["bss_score_disinhibition"] = mean_columns_complete(df, ["bss_4", "bss_8"])
    return df


def add_phys_anhed_scores(df: pd.DataFrame) -> pd.DataFrame:
    # RPAS short: 15 items with mixed reverse coding
    part1 = ["phys_anhed_5", "phys_anhed_6", "phys_anhed_8", "phys_anhed_10"]
    part2 = [
        "phys_anhed_1",
        "phys_anhed_2",
        "phys_anhed_3",
        "phys_anhed_4",
        "phys_anhed_7",
        "phys_anhed_9",
        "phys_anhed_11",
        "phys_anhed_12",
        "phys_anhed_13",
        "phys_anhed_14",
        "phys_anhed_15",
    ]
    s1 = sum_columns_complete(df, part1)
    s2 = sum_columns_complete_transform(df, part2, reverse_0_to_1)
    df["rpasShort_score_total"] = (s1 + s2).where(s1.notna() & s2.notna())
    return df


def add_soc_anhed_scores(df: pd.DataFrame) -> pd.DataFrame:
    # RSAS short: 15 items with mixed reverse coding
    part1 = [
        "soc_anhed_1",
        "soc_anhed_2",
        "soc_anhed_3",
        "soc_anhed_5",
        "soc_anhed_6",
        "soc_anhed_7",
        "soc_anhed_8",
        "soc_anhed_10",
        "soc_anhed_15",
    ]
    part2 = [
        "soc_anhed_4",
        "soc_anhed_9",
        "soc_anhed_11",
        "soc_anhed_12",
        "soc_anhed_13",
        "soc_anhed_14",
    ]
    s1 = sum_columns_complete(df, part1)
    s2 = sum_columns_complete_transform(df, part2, reverse_0_to_1)
    df["rsasShort_score_total"] = (s1 + s2).where(s1.notna() & s2.notna())
    return df


def add_eswan_dmdd_scores(df: pd.DataFrame) -> pd.DataFrame:
    def seq(tag: str) -> List[str]:
        return [f"eswan_dmdd_{i:02d}{tag}" for i in range(1, 11)]

    # Subtract 4 from each item once (so final TSV has adjusted values); skip if already adjusted
    item_cols = seq("a") + seq("b") + seq("c")
    existing_items = [c for c in item_cols if c in df.columns]
    if existing_items:
        num = df[existing_items].apply(pd.to_numeric, errors="coerce")
        # If any value is negative, data have already been adjusted (prior run)
        if not (num < 0).any().any():
            for c in existing_items:
                df[c] = to_numeric(df[c]) - 4

    def sum_when_all_items_present(columns: List[str]) -> pd.Series:
        existing = [c for c in columns if c in df.columns]
        if not existing or len(existing) != len(columns):
            return pd.Series([math.nan] * len(df), index=df.index)
        num = df[existing].apply(pd.to_numeric, errors="coerce")
        all_present = num.notna().all(axis=1)
        return num.sum(axis=1).where(all_present)

    home = sum_when_all_items_present(seq("a"))
    friend = sum_when_all_items_present(seq("b"))
    school = sum_when_all_items_present(seq("c"))
    df["eswanDMDD_score_homeOutburst"] = home
    df["eswanDMDD_score_friendOutburst"] = friend
    df["eswanDMDD_score_schoolOutburst"] = school
    avg = ((home + friend + school) / 3.0).round(1)
    df["eswanDMDD_score_total"] = avg.where(
        home.notna() & friend.notna() & school.notna()
    )
    return df


def _parse_hhmm_to_hours(value: Optional[float]) -> Optional[float]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        iv = int(value)
    except Exception:
        try:
            iv = int(float(value))  # type: ignore[arg-type]
        except Exception:
            return None
    s = f"{iv:04d}"
    hh = int(s[:2])
    mm = int(s[2:])
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return hh + (mm / 60.0)


def add_psqi_scores(df: pd.DataFrame) -> pd.DataFrame:
    # Component 1
    if "psqi_6" in df:
        df["psqi_score_component1"] = to_numeric(
            df["psqi_6"]
        )  # subjective sleep quality
    else:
        df["psqi_score_component1"] = math.nan

    # Component 2
    comp2_1 = pd.Series([math.nan] * len(df), index=df.index)
    if "psqi_2" in df:
        mins = to_numeric(df["psqi_2"])  # minutes to fall asleep
        comp2_1 = pd.Series([math.nan] * len(df), index=df.index)
        comp2_1 = comp2_1.mask(~mins.isna() & (mins <= 15), 0)
        comp2_1 = comp2_1.mask(~mins.isna() & (mins >= 16) & (mins <= 30), 1)
        comp2_1 = comp2_1.mask(~mins.isna() & (mins >= 31) & (mins <= 60), 2)
        comp2_1 = comp2_1.mask(~mins.isna() & (mins > 60), 3)

    comp2_2 = (
        to_numeric(df["psqi_5a"])
        if "psqi_5a" in df
        else pd.Series([math.nan] * len(df), index=df.index)
    )
    comp2_3 = comp2_1 + comp2_2
    comp2 = pd.Series([math.nan] * len(df), index=df.index)
    comp2 = comp2.mask(~comp2_3.isna() & (comp2_3 == 0), 0)
    comp2 = comp2.mask(~comp2_3.isna() & (comp2_3.isin([1, 2])), 1)
    comp2 = comp2.mask(~comp2_3.isna() & (comp2_3.isin([3, 4])), 2)
    comp2 = comp2.mask(~comp2_3.isna() & (comp2_3.isin([5, 6])), 3)
    df["psqi_score_component2"] = comp2

    # Component 3 (sleep duration)
    comp3 = pd.Series([math.nan] * len(df), index=df.index)
    if "psqi_4" in df:
        hours = to_numeric(df["psqi_4"])  # hours slept
        comp3 = comp3.mask(~hours.isna() & (hours > 7), 0)
        comp3 = comp3.mask(~hours.isna() & (hours >= 6) & (hours <= 7), 1)
        comp3 = comp3.mask(~hours.isna() & (hours >= 4) & (hours <= 5), 2)
        comp3 = comp3.mask(~hours.isna() & (hours < 5), 3)
    df["psqi_score_component3"] = comp3

    # Component 4 (habitual sleep efficiency)
    bed_hours = df.get("psqi_1")
    wake_hours = df.get("psqi_3")
    slept_hours = to_numeric(df.get("psqi_4")) if "psqi_4" in df else None
    eff_series = pd.Series([math.nan] * len(df), index=df.index)
    if bed_hours is not None and wake_hours is not None and slept_hours is not None:
        bed_dec = bed_hours.apply(_parse_hhmm_to_hours)
        wake_dec = wake_hours.apply(_parse_hhmm_to_hours)
        in_bed = []
        for b, w in zip(bed_dec, wake_dec):
            if b is None or w is None:
                in_bed.append(math.nan)
                continue
            if w >= b:
                in_bed.append(w - b)
            else:
                in_bed.append((24.0 - b) + w)
        in_bed_series = pd.Series(in_bed, index=df.index)
        with pd.option_context("mode.use_inf_as_na", True):
            eff_series = (slept_hours / in_bed_series) * 100.0

    comp4 = pd.Series([math.nan] * len(df), index=df.index)
    comp4 = comp4.mask(~eff_series.isna() & (eff_series > 85.0), 0)
    comp4 = comp4.mask(
        ~eff_series.isna() & (eff_series <= 84.0) & (eff_series >= 75.0), 1
    )
    comp4 = comp4.mask(
        ~eff_series.isna() & (eff_series <= 74.0) & (eff_series >= 65.0), 2
    )
    comp4 = comp4.mask(~eff_series.isna() & (eff_series < 65.0), 3)
    df["psqi_score_component4"] = comp4

    # Component 5 (sleep disturbances: 5b..5i and 5othera)
    disturb_cols = [
        "psqi_5b",
        "psqi_5c",
        "psqi_5d",
        "psqi_5e",
        "psqi_5f",
        "psqi_5g",
        "psqi_5h",
        "psqi_5i",
        "psqi_5othera",
    ]
    disturb_sum = sum_columns_complete(df, disturb_cols)
    comp5 = pd.Series([math.nan] * len(df), index=df.index)
    comp5 = comp5.mask(~disturb_sum.isna() & (disturb_sum == 0), 0)
    comp5 = comp5.mask(~disturb_sum.isna() & (disturb_sum >= 1) & (disturb_sum <= 9), 1)
    comp5 = comp5.mask(
        ~disturb_sum.isna() & (disturb_sum >= 10) & (disturb_sum <= 18), 2
    )
    comp5 = comp5.mask(
        ~disturb_sum.isna() & (disturb_sum >= 19) & (disturb_sum <= 27), 3
    )
    df["psqi_score_component5"] = comp5

    # Component 6: use of sleeping medication (psqi_7)
    df["psqi_score_component6"] = (
        to_numeric(df["psqi_7"]) if "psqi_7" in df else math.nan
    )

    # Component 7: daytime dysfunction (psqi_8 + psqi_9)
    comp7_sum = sum_columns_complete(df, ["psqi_8", "psqi_9"])
    comp7 = pd.Series([math.nan] * len(df), index=df.index)
    comp7 = comp7.mask(~comp7_sum.isna() & (comp7_sum == 0), 0)
    comp7 = comp7.mask(~comp7_sum.isna() & (comp7_sum >= 1) & (comp7_sum <= 2), 1)
    comp7 = comp7.mask(~comp7_sum.isna() & (comp7_sum >= 3) & (comp7_sum <= 4), 2)
    comp7 = comp7.mask(~comp7_sum.isna() & (comp7_sum >= 5) & (comp7_sum <= 6), 3)
    df["psqi_score_component7"] = comp7

    # Global score
    comp_cols = [
        "psqi_score_component1",
        "psqi_score_component2",
        "psqi_score_component3",
        "psqi_score_component4",
        "psqi_score_component5",
        "psqi_score_component6",
        "psqi_score_component7",
    ]
    df["psqi_score_global"] = sum_columns_complete(df, comp_cols)
    return df


def add_best_ms_scores(df: pd.DataFrame) -> pd.DataFrame:
    sub_a = [f"best_ms_{i}" for i in range(1, 9)]
    sub_b = [f"best_ms_{i}" for i in range(9, 13)]
    a_sum = sum_columns_complete(df, sub_a)
    b_sum = sum_columns_complete(df, sub_b)
    df["best_score_subscaleA"] = a_sum
    df["best_score_subscaleB"] = b_sum
    df["best_score_finalNoComponentC"] = (a_sum + b_sum).where(
        a_sum.notna() & b_sum.notna()
    )
    return df


def add_biss_madrs_scores(df: pd.DataFrame) -> pd.DataFrame:
    # Reorder columns: participant_id, then biss_1..biss_43, then madrs_1..madrs_10
    # (BISS in this dataset has 43 items, not 44)
    biss_cols = [f"biss_{i}" for i in range(1, 44)]
    madrs_cols = [f"madrs_{i}" for i in range(1, 11)]
    ordered = []
    if PARTICIPANT_ID_COL in df.columns:
        ordered.append(PARTICIPANT_ID_COL)
    ordered += [c for c in biss_cols if c in df.columns]
    ordered += [c for c in madrs_cols if c in df.columns]
    other = [c for c in df.columns if c not in ordered]
    df = df[ordered + other]

    df["biss_depression"] = sum_columns_complete(df, biss_cols[:22])  # biss_1..biss_22
    df["biss_mania"] = sum_columns_complete(df, biss_cols[22:])  # biss_23..biss_43
    df["madrs_total"] = sum_columns_complete(df, madrs_cols)
    return df


InstrumentScorer = Callable[[pd.DataFrame], pd.DataFrame]


SCORERS: Dict[str, InstrumentScorer] = {
    # instrument_stem -> function
    "als": add_als_scores,
    "mapssr": add_mapsr_scores,
    "swan": add_swan_scores,
    "aces": add_aces_scores,
    "scared": add_scared_scores,
    "rpaq": add_rpaq_scores,
    "ari": add_ari_scores,
    "bdi": add_bdi_scores,
    "bisbas": add_bisbas_scores,
    "grit": add_grit_scores,
    "hcl16": add_hcl16_scores,
    "bss": add_bss_scores,
    "phys_anhed": add_phys_anhed_scores,
    "soc_anhed": add_soc_anhed_scores,
    "eswan_dmdd": add_eswan_dmdd_scores,
    "psqi": add_psqi_scores,
    "best_ms": add_best_ms_scores,
    "biss_madrs": add_biss_madrs_scores,
}


def score_file(path: Path, out_dir: Path) -> Optional[Path]:
    if path.suffix.lower() != ".tsv":
        return None
    instrument = path.stem
    scorer = SCORERS.get(instrument)
    if scorer is None:
        return None

    df = pd.read_csv(path, sep="\t", dtype={PARTICIPANT_ID_COL: str})
    df = _fill_empty_with_na(df)
    original_cols = list(df.columns)

    # Detect rows that are entirely empty prior to scoring (ignoring participant_id)
    check_cols = [c for c in original_cols if c != PARTICIPANT_ID_COL]
    if check_cols:
        per_col_empty = []
        for col in check_cols:
            s = df[col]
            if s.dtype == object:
                # Treat NaN, empty/whitespace-only, or BIDS "n/a" as empty
                per_col_empty.append(
                    s.isna()
                    | s.astype(str).str.strip().eq("")
                    | s.astype(str).str.strip().str.lower().eq("n/a")
                )
            else:
                per_col_empty.append(s.isna())
        empty_row_mask = per_col_empty[0]
        for e in per_col_empty[1:]:
            empty_row_mask = empty_row_mask & e
    else:
        empty_row_mask = pd.Series([False] * len(df), index=df.index)

    df = scorer(df)

    # Reorder: preserve current column order for original cols (scorer may have reordered), then new ones
    new_cols = [c for c in df.columns if c not in original_cols]
    ordered = [c for c in df.columns if c in original_cols] + new_cols
    df = df[ordered]

    # Clear newly added summary columns for rows that were empty before scoring
    if new_cols:
        for c in new_cols:
            s = df[c]
            # Prefer pandas NA for nullable integer types; NaN otherwise
            if "Int" in str(s.dtype):
                df[c] = s.mask(empty_row_mask, other=pd.NA)
            else:
                df[c] = s.mask(empty_row_mask, other=math.nan)
    df = df[ordered]

    # BIDS: empty summary scores and any remaining missing → "n/a"
    # Convert column-by-column so Int64 (and other non-object) columns can hold "n/a"
    for c in df.columns:
        df[c] = df[c].astype(object).fillna("n/a")

    out_path = out_dir / path.name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, sep="\t", index=False)
    return out_path


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir or args.input_dir

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory not found: {input_dir}")
        return 2

    if args.file is not None:
        path = Path(args.file)
        if not path.is_absolute():
            path = input_dir / path.name
        if path.suffix.lower() != ".tsv":
            print(f"Not a TSV file: {args.file}")
            return 2
        if not path.exists():
            print(f"File not found: {path}")
            return 2
        tsv_files = [path]
    else:
        tsv_files = sorted(input_dir.glob("*.tsv"))

    if not tsv_files:
        print(f"No TSV files found in {input_dir}")
        return 0

    wrote = 0
    skipped: List[str] = []
    for f in tsv_files:
        out = score_file(f, output_dir)
        if out is None:
            skipped.append(f.name)
            continue
        wrote += 1

    print(
        f"Scored {wrote} instrument file(s) in {output_dir}. "
        + (f"Skipped: {', '.join(skipped)}" if skipped else "")
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(main(sys.argv[1:]))
