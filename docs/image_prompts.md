# Figure-generation prompts (methodology / system-design figures)

> The paper currently embeds matplotlib-drawn versions
> (`analysis/make_method_diagrams.py` → `fig13/fig14/fig15`).
> Use the prompts below with any diagram-capable image model to produce
> polished replacements. Keep the **same filenames and meaning** — only
> restyle. IEEE two-column: target width ≈ 3.4 in (single column),
> sans-serif labels, print-friendly palette (no photo backgrounds).

## Fig. 13 — End-to-end research pipeline (`fig13_method_pipeline.png`)

```
Flat vector-style horizontal flowchart, 5 rounded boxes with arrows, white
background, IEEE paper figure aesthetic, navy/blue-gray palette:
Box 1 "Task design — 150 candidates, 5 categories";
Box 2 "Multi-turn interaction — 4 LLMs × C0–C4";
Box 3 (highlighted amber) "Corpus cleaning — 1418 in scope, 67 artifacts out";
Box 4 "RAPL measurement — K=5 + warm-up, 1307 programs";
Box 5 (green) "Analysis + paper".
Clean sans-serif text, no shadows, no logos.
```

## Fig. 14 — Per-unit interaction protocol (`fig14_interaction_protocol.png`)

```
Vertical swimlane diagram with 3 columns (Prompt turn → LLM turn(s) →
final.py snapshot) and 5 rows:
C0 ONE_SHOT (single prompt → LLM turn → code.py);
C1 BUG_FIX (buggy code + fix request);
C2 FEATURE_ADDITION (working code + feature);
C3 EDGE_CASE (working code + edge cases);
C4 FULL MULTI-TURN (bug → fix → feature → edge).
Note under title: "fresh conversation per cell".
Flat vector style, white background, navy accents, sans-serif.
```

## Fig. 15 — Isolated measurement setup (`fig15_measurement_setup.png`)

```
Small system-block diagram, flat vector style, white background:
left box "final.py + task fixture (small/med/large inputs)" arrow to center
box "harness runner — warm-up + K=5 reps, 30 s cap, median";
center splits to two green boxes "Intel RAPL package energy_uj (delta per
rep)" and "/usr/bin/time -f %M peak RSS"; both arrow to right box
"energy / runtime / memory".
Monospace font for paths/commands, navy/green palette, no hardware photos.
```
