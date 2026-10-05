# AI figure-generation prompts (methodology diagrams fig13–fig15)

Generate each image with any image model (Midjourney / DALL·E / Stable
Diffusion / Gemini / Firefly), then save as PNG and overwrite the files below
**keeping the exact filenames** — the papers pick them up automatically:

| Figure | Overwrite these two files |
|---|---|
| fig13 pipeline | `latex/images/fig13_method_pipeline.png` + `docx/images/fig13_method_pipeline.png` |
| fig14 protocol | `latex/images/fig14_interaction_protocol.png` + `docx/images/fig14_interaction_protocol.png` |
| fig15 measurement | `latex/images/fig15_measurement_setup.png` + `docx/images/fig15_measurement_setup.png` |

Global style for all three (paste into every prompt):
> Flat vector infographic, clean white background, IEEE paper figure
> aesthetic, navy blue (#1F4E79) + slate gray + one amber/green accent,
> sans-serif typography (Arial/Helvetica-like), sharp edges, no shadows,
> no gradients, no photo elements, no logos, no watermarks.
> All text must be spelled EXACTLY as given below — no lorem ipsum,
> no invented words. Landscape orientation, ≥2000 px wide, PNG.

---

## Prompt 1 — fig13_method_pipeline.png (end-to-end research pipeline)

> Flat vector horizontal flowchart, 5 rounded-rectangle boxes connected by
> rightward arrows, white background, IEEE paper figure aesthetic, navy
> (#1F4E79) borders with light-blue fill, one amber-highlighted box,
> one green final box, sans-serif text, no shadows, no logos.
> Exact box texts, in order:
> 1. "Task design / 150 candidates / 5 categories"
> 2. "Multi-turn interaction / 4 LLMs x C0-C4"
> 3. (amber) "Corpus cleaning / 1418 in scope / 67 artifacts out"
> 4. "RAPL measurement / K=5 + warm-up / 1307 programs"
> 5. (green) "Analysis + paper"
> Title above: "End-to-end research pipeline".
> Landscape, 2048x1024, PNG. Spell every word exactly as written.

## Prompt 2 — fig14_interaction_protocol.png (per-unit interaction protocol)

> Flat vector swimlane diagram, white background, IEEE paper figure
> aesthetic, navy (#1F4E79) accents, sans-serif text, no shadows, no logos.
> Three columns left to right: "Prompt turn", "LLM turn(s)",
> "final.py snapshot". Five rows top to bottom with exact row labels:
> Row 1: "C0 ONE-SHOT — single prompt"
> Row 2: "C1 BUG-FIX — buggy code + fix request"
> Row 3: "C2 FEATURE-ADDITION — working code + feature"
> Row 4: "C3 EDGE-CASE — working code + edge cases"
> Row 5: "C4 FULL MULTI-TURN — bug, fix, feature, edge"
> Small note under the title: "fresh conversation per cell".
> Title above: "Per-unit interaction protocol".
> Landscape, 2048x1400, PNG. Spell every word exactly as written.

## Prompt 3 — fig15_measurement_setup.png (isolated measurement setup)

> Flat vector system block diagram, white background, IEEE paper figure
> aesthetic, navy (#1F4E79) and green accents, monospace font for
> paths/commands, sans-serif otherwise, no shadows, no hardware photos,
> no logos. Layout left to right with arrows:
> Left box: "final.py + task fixture (small / medium / large inputs)"
> arrow to center box:
> Center box: "harness runner — warm-up + K=5 reps, 30 s cap, median"
> splitting with arrows to two green boxes stacked vertically:
> Green box A: "Intel RAPL package — energy_uj delta per rep"
> Green box B: "/usr/bin/time -f %M peak RSS"
> both arrow to right box: "energy / runtime / memory".
> Title above: "Isolated energy-measurement setup".
> Landscape, 2048x1024, PNG. Spell every word exactly as written,
> keep "%M" exactly.

---

## Tips

- If the model garbles text, regenerate with "large clear text, generous
  letter spacing" appended, or build the layout in PowerPoint/Canva using
  the exact texts above and export PNG.
- Keep the same filenames — `make_paper_pro.py`, both `.tex` files, and
  the List of Figures all reference them already; just rebuild the DOCX
  (`python3 scripts/make_paper_pro.py`) after replacing.
