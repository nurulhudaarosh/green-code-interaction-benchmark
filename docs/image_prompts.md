# Image generation brief (fig13–fig15)

Copy everything below into your image AI's prompt box (or attach it as a
reference file). It first explains how the project works, then asks for
three icon-driven illustrations. Save each result as PNG and overwrite
**both copies keeping the exact filenames** (papers already reference them):

| Figure | Overwrite these two files |
|---|---|
| fig13 | `latex/images/fig13_method_pipeline.png` + `docx/images/fig13_method_pipeline.png` |
| fig14 | `latex/images/fig14_interaction_protocol.png` + `docx/images/fig14_interaction_protocol.png` |
| fig15 | `latex/images/fig15_measurement_setup.png` + `docx/images/fig15_measurement_setup.png` |

--- COPY BELOW THIS LINE ---

You are illustrating a research project for an IEEE paper. First,
understand how the project works:

HOW THE PROJECT WORKS: Researchers want to know whether chatting longer
with an AI coding assistant makes the final program consume more
electricity. They built the "Green Code Interaction Benchmark": 150
programming tasks across 5 categories (algorithms, file/data processing,
image/media processing, realistic apps, text/log processing). Four AI
models (GPT, Claude, Gemini, DeepSeek) solve every task under 5
interaction styles ending at the SAME final specification: C0 one-shot
(single prompt), C1 bug-fix, C2 feature-addition, C3 edge-case handling,
C4 full multi-turn (bug then fix then feature then edge cases). That
gives 1418 final programs. Each program is executed alone on identical
deterministic workloads on one Linux machine (Intel i5), and its CPU
package energy is read from Intel RAPL hardware counters (warm-up + 5
timed runs, median reported), plus runtime and peak memory. Bad data
(67 collection mistakes like prose instead of code) is thrown out; 1307
programs measured, 111 genuine AI bugs kept for failure analysis.
Findings: full multi-turn finals use ~32% more median energy than
one-shot (mean +64%, heavy tail), energy follows runtime almost exactly,
multi-turn code fails ~5x more often (15.8% vs 3.4%), and total measured
energy equals ~247 mg of CO2.

NOW generate three beautiful, modern flat icon illustrations (soft
green-blue gradient backgrounds, minimal, elegant, IEEE paper figures,
tiny sans-serif labels only, no paragraphs, no logos, landscape,
>=2000 px wide, PNG):

IMAGE 1 (fig13 — the research journey): one flowing left-to-right scene:
a task clipboard, a robot-assistant chat bubble, a data-cleaning filter
funnel, a glowing green CPU chip with a lightning bolt, and a paper with
charts under a graduation cap, linked by a soft dotted path. Tiny
labels: "Tasks", "AI interaction", "Cleaning", "Energy measure",
"Paper". Title: "From interaction to energy insight".

IMAGE 2 (fig14 — same goal, different journey): a split scene. Left: a
single chat bubble producing a small tidy code file with a green leaf
(efficient). Right: a long winding chat with bug, feature and edge-case
icons producing a bulky code file with a rising energy meter. Tiny
labels: "One-shot", "Full multi-turn". Title: "Same specification,
different journey".

IMAGE 3 (fig15 — measuring every joule): a laptop running Python code
connected by glowing lines to a large CPU chip with a green lightning
bolt, beside a stopwatch and a small watt gauge, faint binary pattern
behind. Tiny labels: "Python program", "Intel RAPL", "K=5 runs".
Title: "Measuring every joule".

Spell every label exactly as written. If any text renders garbled,
regenerate that image.

--- COPY ABOVE THIS LINE ---

## After replacing the PNGs

Rebuild the DOCX once: `python3 scripts/make_paper_pro.py`
(LaTeX needs no change — filenames are already referenced).
