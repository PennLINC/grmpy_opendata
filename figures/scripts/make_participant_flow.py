from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import patches


# Edit this block when counts change. The fMRI counts below repeat the
# single fMRI counts from the Illustrator figure as placeholders.
AVAILABLE_N = 231

STAGES = [
    ("raw", "RAW DATA"),
    ("processed", "PROCESSED"),
    ("qc", "PASSING QC"),
]


@dataclass(frozen=True)
class SingleModality:
    label: str
    color: str
    counts: dict[str, int]


@dataclass(frozen=True)
class Acquisition:
    label: str
    counts: dict[str, int]


@dataclass(frozen=True)
class MultiAcquisitionModality:
    label: str
    color: str
    acquisitions: list[Acquisition]


MODALITIES: list[SingleModality | MultiAcquisitionModality] = [
    SingleModality(
        label="sMRI",
        color="#e88972",
        counts={"raw": 231, "processed": 230, "qc": 175},
    ),
    MultiAcquisitionModality(
        label="fMRI",
        color="#f4ef8a",
        acquisitions=[
            Acquisition("rest-\nmultiband", {"raw": 230, "processed": 230, "qc": 229}),
            Acquisition("rest-\nsingleband", {"raw": 230, "processed": 230, "qc": 229}),
            Acquisition("fracback", {"raw": 230, "processed": 230, "qc": 229}),
            Acquisition("face", {"raw": 230, "processed": 230, "qc": 229}),
        ],
    ),
    SingleModality(
        label="DWI",
        color="#a7d29b",
        counts={"raw": 231, "processed": 176, "qc": 176},
    ),
    SingleModality(
        label="ASL",
        color="#ee93bf",
        counts={"raw": 214, "processed": 190, "qc": 177},
    ),
]


def blend_with_white(hex_color: str, amount: float) -> tuple[float, float, float]:
    """Return color blended toward white by amount in [0, 1]."""
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(channel * (1 - amount) + amount for channel in rgb)


def draw_box(
    ax: plt.Axes,
    left: float,
    center_y: float,
    width: float,
    height: float,
    facecolor,
    text: str,
    *,
    fontsize: float = 9,
    weight: str = "normal",
    edgecolor: str = "#2f3538",
    linewidth: float = 1.05,
) -> None:
    bottom = center_y - height / 2
    rect = patches.Rectangle(
        (left, bottom),
        width,
        height,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
        joinstyle="miter",
    )
    ax.add_patch(rect)
    ax.text(
        left + width / 2,
        center_y,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        color="#1c2529",
    )


def draw_down_arrow(
    ax: plt.Axes,
    x: float,
    y_start: float,
    y_end: float,
    *,
    scale: float = 12,
    linewidth: float = 1.35,
) -> None:
    ax.annotate(
        "",
        xy=(x, y_end),
        xytext=(x, y_start),
        arrowprops={
            "arrowstyle": "-|>",
            "color": "black",
            "linewidth": linewidth,
            "shrinkA": 0,
            "shrinkB": 0,
            "mutation_scale": scale,
        },
    )


def draw_participant_flow(output_dir: Path) -> list[Path]:
    plt.rcParams.update(
        {
            "font.family": ["Arial", "DejaVu Sans"],
            "mathtext.default": "it",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(12.4, 5.1))
    ax.set_xlim(0, 12.4)
    ax.set_ylim(0, 9.6)
    ax.axis("off")

    stage_y = {"raw": 6.95, "processed": 4.85, "qc": 2.75}
    box_h = 0.78
    single_w = 1.82
    single_gap = 0.55
    fmri_cell_w = 0.78
    fmri_cell_gap = 0.13
    fmri_group_w = 4 * fmri_cell_w + 3 * fmri_cell_gap

    x_positions: dict[str, tuple[float, float]] = {}
    x = 0.98
    for modality in MODALITIES:
        if isinstance(modality, SingleModality):
            width = single_w
        else:
            width = fmri_group_w
        x_positions[modality.label] = (x, width)
        x += width + single_gap

    right_edge = x - single_gap

    top_left = 0.18
    top_bottom = 8.55
    top_h = 0.8
    top_w = right_edge - top_left + 0.30
    draw_box(
        ax,
        top_left,
        top_bottom + top_h / 2,
        top_w,
        top_h,
        "#dfeef3",
        rf"Available participants ($n$ = {AVAILABLE_N})",
        fontsize=10,
        weight="bold",
        linewidth=1.1,
    )

    label_x = 0.18
    label_w = 0.42
    for key, label in STAGES:
        label_bottom = stage_y[key] - 1.22 / 2
        ax.add_patch(
            patches.Rectangle(
                (label_x, label_bottom),
                label_w,
                1.22,
                facecolor="#dfeef3",
                edgecolor="#2f3538",
                linewidth=0.95,
                joinstyle="miter",
            )
        )
        ax.text(
            label_x + label_w / 2,
            stage_y[key],
            label,
            ha="center",
            va="center",
            rotation=90,
            fontsize=6.4,
            fontweight="bold",
            color="#1c2529",
        )

    row_blends = {"raw": 0.0, "processed": 0.38, "qc": 0.72}
    top_arrow_start = top_bottom
    raw_arrow_end = stage_y["raw"] + box_h / 2 + 0.05
    row_arrow_gap = 0.13

    for modality in MODALITIES:
        left, width = x_positions[modality.label]
        center_x = left + width / 2
        if isinstance(modality, SingleModality):
            for key, _ in STAGES:
                draw_box(
                    ax,
                    left,
                    stage_y[key],
                    width,
                    box_h,
                    blend_with_white(modality.color, row_blends[key]),
                    rf"$n_{{participants}}$ = {modality.counts[key]}",
                    fontsize=8.1,
                )

            draw_down_arrow(ax, center_x, top_arrow_start, raw_arrow_end)
            draw_down_arrow(
                ax,
                center_x,
                stage_y["raw"] - box_h / 2 - row_arrow_gap,
                stage_y["processed"] + box_h / 2 + row_arrow_gap,
            )
            draw_down_arrow(
                ax,
                center_x,
                stage_y["processed"] - box_h / 2 - row_arrow_gap,
                stage_y["qc"] + box_h / 2 + row_arrow_gap,
            )

            draw_box(
                ax,
                center_x - 0.43,
                1.18,
                0.86,
                0.38,
                "#dfeef3",
                modality.label,
                fontsize=9.5,
                weight="bold",
                linewidth=1.0,
            )
        else:
            acq_centers: list[float] = []
            for i, acquisition in enumerate(modality.acquisitions):
                acq_left = left + i * (fmri_cell_w + fmri_cell_gap)
                acq_center = acq_left + fmri_cell_w / 2
                acq_centers.append(acq_center)
                for key, _ in STAGES:
                    draw_box(
                        ax,
                        acq_left,
                        stage_y[key],
                        fmri_cell_w,
                        box_h,
                        blend_with_white(modality.color, row_blends[key]),
                        rf"$n$ = {acquisition.counts[key]}",
                        fontsize=7.4,
                    )
                draw_down_arrow(
                    ax,
                    acq_center,
                    stage_y["raw"] - box_h / 2 - row_arrow_gap,
                    stage_y["processed"] + box_h / 2 + row_arrow_gap,
                    scale=10,
                    linewidth=1.1,
                )
                draw_down_arrow(
                    ax,
                    acq_center,
                    stage_y["processed"] - box_h / 2 - row_arrow_gap,
                    stage_y["qc"] + box_h / 2 + row_arrow_gap,
                    scale=10,
                    linewidth=1.1,
                )
                draw_box(
                    ax,
                    acq_left,
                    1.55,
                    fmri_cell_w,
                    0.46,
                    "#eef5f7",
                    acquisition.label,
                    fontsize=5.7,
                    weight="bold",
                    linewidth=0.8,
                )

            branch_y = 8.02
            ax.plot(
                [acq_centers[0], acq_centers[-1]],
                [branch_y, branch_y],
                color="black",
                linewidth=1.15,
            )
            draw_down_arrow(ax, center_x, top_arrow_start, branch_y, scale=11)
            for acq_center in acq_centers:
                draw_down_arrow(
                    ax,
                    acq_center,
                    branch_y,
                    raw_arrow_end,
                    scale=9,
                    linewidth=1.05,
                )

            draw_box(
                ax,
                left,
                0.98,
                width,
                0.38,
                "#dfeef3",
                modality.label,
                fontsize=9.5,
                weight="bold",
                linewidth=1.0,
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        output_dir / "fig4.png",
        output_dir / "fig4.pdf",
        output_dir / "fig4.svg",
    ]
    for path in outputs:
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create participant-flow figure.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("illustrator/png"),
        help="Directory for PNG, PDF, and SVG outputs. Defaults to illustrator/png.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    for saved_path in draw_participant_flow(args.output_dir.expanduser()):
        print(saved_path.resolve())
