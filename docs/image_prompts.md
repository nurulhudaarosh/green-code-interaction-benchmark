# AI figure-generation prompts (methodology diagrams fig13–fig15)

Style direction: **beautiful, icon-driven conceptual illustrations** — NOT
boring box-and-arrow flowcharts. Give the AI the *idea* and let it design
freely with icons and visual metaphors. Keep on-screen text SHORT (a title
plus tiny labels) so nothing gets garbled.

After generating, save as PNG and overwrite **both copies keeping the exact
filenames** (papers already reference them — no code changes needed):

| Figure | Overwrite these two files |
|---|---|
| fig13 pipeline | `latex/images/fig13_method_pipeline.png` + `docx/images/fig13_method_pipeline.png` |
| fig14 protocol | `latex/images/fig14_interaction_protocol.png` + `docx/images/fig14_interaction_protocol.png` |
| fig15 measurement | `latex/images/fig15_measurement_setup.png` + `docx/images/fig15_measurement_setup.png` |

Global style (append to every prompt):
> Modern flat illustration with icons, soft green-blue gradient background,
> clean minimal composition, IEEE paper figure, generous white space,
> small elegant sans-serif labels only, no paragraphs of text, no logos,
> no watermarks. Landscape, >=2000 px wide, PNG.

---

## Prompt 1 — fig13_method_pipeline.png (research journey)

> A beautiful wide illustration of an AI-coding energy research journey,
> left to right as one flowing scene with glowing icons: a clipboard with
> coding tasks, a chat bubble with a robot assistant, a filter funnel
> cleaning data, a glowing green CPU chip with a lightning bolt, and a
> graduation-cap paper with charts at the end, connected by a soft dotted
> path. Tiny labels under icons: "Tasks", "AI interaction",
> "Cleaning", "Energy measure", "Paper". Title on top:
> "From interaction to energy insight". Soft green-blue gradient
> background, flat icon style, minimal, elegant.

## Prompt 2 — fig14_interaction_protocol.png (one-shot vs multi-turn)

> A beautiful split-scene illustration comparing one-shot vs multi-turn AI
> coding: left side shows a single chat bubble producing a small tidy code
> file with one green leaf (efficient); right side shows a long winding
> chat thread with bug, feature and edge-case icons producing a large
> bulky code file with a rising energy meter. Tiny labels: "One-shot",
> "Full multi-turn". Title on top: "Same specification, different
> journey". Flat icon style, soft green-blue gradient background,
> minimal, elegant, IEEE paper figure.

## Prompt 3 — fig15_measurement_setup.png (energy measurement)

> A beautiful illustration of measuring a program's energy: a laptop
> running Python code connected by glowing lines to a large CPU chip with
> a green lightning bolt and a stopwatch, a small gauge showing watts,
> subtle binary-code pattern in the background. Tiny labels: "Python
> program", "Intel RAPL", "K=5 runs". Title on top: "Measuring every
> joule". Flat icon style, soft green-blue gradient background,
> minimal, elegant, IEEE paper figure.

---

## Tips

- If text comes out garbled, regenerate — or delete the text layer and
  add the 2–4 tiny labels yourself in Canva/PowerPoint (takes 2 minutes).
- After replacing the PNGs, rebuild the DOCX once:
  `python3 scripts/make_paper_pro.py` (LaTeX needs no change).
