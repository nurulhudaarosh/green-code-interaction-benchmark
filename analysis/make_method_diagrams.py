#!/usr/bin/env python3
"""Methodology / system-design diagrams for the paper (matplotlib-drawn).

  fig13_method_pipeline.png  end-to-end research pipeline
  fig14_interaction_protocol.png  per-unit interaction protocol (C0..C4)
  fig15_measurement_setup.png  RAPL measurement setup

Written to docx/images/ + latex/images/. Style: print-friendly boxes.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTS = [REPO / "docx" / "images", REPO / "latex" / "images"]
for o in OUTS:
    o.mkdir(parents=True, exist_ok=True)

BOX = dict(boxstyle="round,pad=0.35", fc="#dbeafe", ec="#1e40af", lw=1.4)
DBOX = dict(boxstyle="round,pad=0.35", fc="#fef3c7", ec="#b45309", lw=1.4)
GBOX = dict(boxstyle="round,pad=0.35", fc="#dcfce7", ec="#15803d", lw=1.4)


def save(fig, name):
    for o in OUTS:
        fig.savefig(o / name, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#111827"))


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3); ax.axis("off")
    steps = [
        (1.1, "Task design\n150 candidates\n5 categories", BOX),
        (3.2, "Multi-turn\ninteraction\n4 LLMs x C0-C4", BOX),
        (5.3, "Corpus cleaning\n1418 in scope\n67 artifacts out", DBOX),
        (7.4, "RAPL measure\nK=5 + warm-up\n1307 programs", BOX),
        (9.2, "Analysis\n+ paper", GBOX),
    ]
    xs = [s[0] for s in steps]
    for x, t, st in steps:
        ax.text(x, 1.5, t, ha="center", va="center", fontsize=9, bbox=st)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, a + 0.85, 1.5, b - 0.85, 1.5)
    ax.set_title("End-to-end research pipeline", fontsize=12, fontweight="bold")
    save(fig, "fig13_method_pipeline.png")


def fig_protocol():
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.4); ax.axis("off")
    ax.set_title("Per-unit interaction protocol (fresh conversation per cell)",
                 fontsize=12, fontweight="bold")
    ax.text(1.2, 5.5, "C0 ONE_SHOT\nsingle prompt", ha="center", va="center",
            fontsize=9, bbox=BOX)
    for i, (t, y) in enumerate([("C1 BUG_FIX\nbuggy code + fix request", 4.2),
                                ("C2 FEATURE_ADDITION\nworking code + feature", 3.1),
                                ("C3 EDGE_CASE\nworking code + edge cases", 2.0),
                                ("C4 FULL MULTI-TURN\nbug -> fix -> feature -> edge", 0.9)]):
        ax.text(1.2, y, t, ha="center", va="center", fontsize=9, bbox=BOX)
        ax.text(4.6, y, "LLM turn(s)", ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#6b7280"))
        ax.text(7.6, y, "final.py\n(snapshot)", ha="center", va="center",
                fontsize=9, bbox=GBOX)
        arrow(ax, 2.35, y, 3.75, y)
        arrow(ax, 5.45, y, 6.85, y)
    ax.text(1.2, 5.5, "C0 ONE_SHOT\nsingle prompt", ha="center", va="center",
            fontsize=9, bbox=BOX)
    ax.text(4.6, 5.5, "LLM turn", ha="center", va="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#6b7280"))
    ax.text(7.6, 5.5, "code.py", ha="center", va="center", fontsize=9, bbox=GBOX)
    arrow(ax, 2.35, 5.5, 3.75, 5.5)
    arrow(ax, 5.45, 5.5, 6.85, 5.5)
    save(fig, "fig14_interaction_protocol.png")


def fig_measure():
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.4); ax.axis("off")
    ax.set_title("Isolated energy-measurement setup (one program at a time)",
                 fontsize=12, fontweight="bold")
    ax.text(1.4, 1.6, "final.py\n+ task fixture\n(small/med/large)", ha="center",
            va="center", fontsize=9, bbox=BOX)
    ax.text(4.2, 1.6, "harness runner\nwarm-up + K=5 reps\n30 s cap, median", ha="center",
            va="center", fontsize=9, bbox=DBOX)
    ax.text(7.0, 2.2, "Intel RAPL pkg\nenergy_uj\n(delta per rep)", ha="center",
            va="center", fontsize=9, bbox=GBOX)
    ax.text(7.0, 0.9, "/usr/bin/time -f %M\npeak RSS", ha="center", va="center",
            fontsize=9, bbox=GBOX)
    ax.text(9.2, 1.6, "energy /\nruntime /\nmemory", ha="center", va="center",
            fontsize=9, bbox=dict(boxstyle="round,pad=0.35", fc="white",
                                 ec="#111827", lw=1.4))
    arrow(ax, 2.5, 1.6, 3.1, 1.6)
    arrow(ax, 5.3, 1.8, 6.1, 2.1)
    arrow(ax, 5.3, 1.4, 6.1, 1.0)
    arrow(ax, 7.9, 2.0, 8.55, 1.7)
    arrow(ax, 7.9, 1.1, 8.55, 1.5)
    save(fig, "fig15_measurement_setup.png")


if __name__ == "__main__":
    fig_pipeline()
    fig_protocol()
    fig_measure()
