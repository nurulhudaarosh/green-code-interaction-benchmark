# Image prompts (fig13–fig15) — 3 separate copy-paste blocks

Each block below is self-contained: it explains the project part the AI
needs, then asks for that one image. Generate one image per block, save as
PNG, and overwrite **both copies keeping the exact filenames** (papers
already reference them — no code changes needed):

| Block | Save as |
|---|---|
| Prompt 1 | `latex/images/fig13_method_pipeline.png` + `docx/images/fig13_method_pipeline.png` |
| Prompt 2 | `latex/images/fig14_interaction_protocol.png` + `docx/images/fig14_interaction_protocol.png` |
| Prompt 3 | `latex/images/fig15_measurement_setup.png` + `docx/images/fig15_measurement_setup.png` |

---

## PROMPT 1 — copy everything below (fig13: research journey)

Our research asks: does chatting longer with an AI coding assistant make
the final program consume more electricity? We built the "Green Code
Interaction Benchmark": 150 programming tasks (algorithms, file/data,
image/media, realistic apps, text/log). Four AI models (GPT, Claude,
Gemini, DeepSeek) solve them; we clean the data (1418 programs kept, 67
collection mistakes removed), measure each program's CPU energy with
Intel RAPL hardware counters (1307 programs), and write the paper
(finding: full multi-turn code uses ~32% more median energy).

Generate ONE beautiful wide illustration of this research journey,
left to right as a single flowing scene with glowing icons: a task
clipboard, a robot-assistant chat bubble, a data-cleaning filter funnel,
a glowing green CPU chip with a lightning bolt, and a paper with charts
under a graduation cap, linked by a soft dotted path. Tiny labels under
the icons: "Tasks", "AI interaction", "Cleaning", "Energy measure",
"Paper". Title on top: "From interaction to energy insight". Modern flat
icon style, soft green-blue gradient background, minimal, elegant, IEEE
paper figure, tiny sans-serif labels only, no logos, landscape,
>=2000 px wide, PNG. Spell every label exactly as written.

---

## PROMPT 2 — copy everything below (fig14: same goal, different journey)

Our benchmark holds the FINAL specification identical and varies only
the interaction trajectory: C0 one-shot (single prompt), C1 bug-fix,
C2 feature-addition, C3 edge-case handling, C4 full multi-turn (bug,
then fix, then feature, then edge cases). Same goal every time —
but the journey differs, and multi-turn finals consume ~32% more median
energy and fail ~5x more often.

Generate ONE beautiful split-scene illustration. Left side: a single
chat bubble producing a small tidy code file with a green leaf
(efficient). Right side: a long winding chat thread with bug, feature
and edge-case icons producing a large bulky code file with a rising
energy meter. Tiny labels: "One-shot", "Full multi-turn". Title on
top: "Same specification, different journey". Modern flat icon style,
soft green-blue gradient background, minimal, elegant, IEEE paper
figure, tiny sans-serif labels only, no logos, landscape, >=2000 px
wide, PNG. Spell every label exactly as written.

---

## PROMPT 3 — copy everything below (fig15: measuring every joule)

Each of our 1418 final programs is executed completely alone on
identical deterministic workloads on one Linux machine (Intel i5, no
other load). Its CPU package energy is read from Intel RAPL hardware
counters: one warm-up run plus K=5 timed runs inside a single counter
window, median reported, 30-second cap — plus runtime and peak memory.
This isolates the program's own energy from all background noise.

Generate ONE beautiful illustration: a laptop running Python code
connected by glowing lines to a large CPU chip with a green lightning
bolt, beside a stopwatch and a small watt gauge, faint binary pattern
in the background. Tiny labels: "Python program", "Intel RAPL",
"K=5 runs". Title on top: "Measuring every joule". Modern flat icon
style, soft green-blue gradient background, minimal, elegant, IEEE
paper figure, tiny sans-serif labels only, no logos, landscape,
>=2000 px wide, PNG. Spell every label exactly as written.

---

## After replacing the PNGs

Rebuild the DOCX once: `python3 scripts/make_paper_pro.py`
(LaTeX needs no change — filenames are already referenced).
