#!/usr/bin/env python3
"""Build per-category member kits (bot-free collection workflow).

Creates kits/<category>/ folders, each containing everything one member
needs on Google Drive / Colab:

    kits/<category>/
    ├── member_collection.ipynb
    ├── dataset/dataset.json
    └── README_MEMBER.txt

Usage:
    python3 scripts/make_member_kit.py            # all categories with a dataset
    python3 scripts/make_member_kit.py SR TL      # only given category codes
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTEBOOK = REPO / "collection" / "member_collection.ipynb"
DATASET_DIR = REPO / "dataset"

CATEGORY_BY_CODE = {
    "FD": "file_data_processing",
    "TL": "text_log_processing",
    "SR": "search_retrieval",
    "AC": "algorithms_computation",
    "IM": "image_media_processing",
    "RA": "realistic_applications_utilities",
}

README = """GREEN CODE BENCHMARK — MEMBER COLLECTION KIT ({code}: {category})
================================================================

Setup (Google Drive + Colab):
1. Copy this WHOLE folder to Google Drive as "Green-Code-Collection"
   (MyDrive/Green-Code-Collection). Keep the structure:
       Green-Code-Collection/
       ├── member_collection.ipynb
       └── dataset/dataset.json
2. Open member_collection.ipynb in Google Colab (or local Jupyter).
3. Run all cells from the top. The notebook resumes automatically
   from .collection/state.json if you disconnect.

Rules:
- Use the EXACT prompts shown by the notebook.
- Start a NEW conversation for every (task, model, interaction) unit.
- Multi-turn: continue the SAME conversation for all turns of one unit.
- Paste the COMPLETE model response (the notebook extracts the code).
- If the notebook warns about multiple/no code blocks, ask the model
  to re-output a single code block; never edit code by hand.
- Never modify dataset/dataset.json.

Finish:
- Run the final cells: validation must pass, then
  "CREATE FINAL SUBMISSION ZIP" produces
  .collection/submissions/collection_submission.zip
- Send that ZIP file to the coordinator.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codes", nargs="*", help="category codes, e.g. SR TL")
    args = ap.parse_args()

    wanted = {c.upper(): CATEGORY_BY_CODE[c.upper()] for c in args.codes} if args.codes else CATEGORY_BY_CODE

    if not NOTEBOOK.is_file():
        print(f"Notebook not found: {NOTEBOOK}")
        return 1

    built = []
    for code, category in wanted.items():
        ds = DATASET_DIR / category / "dataset.json"
        if not ds.is_file() or ds.stat().st_size == 0:
            print(f"skip {code} ({category}): no dataset yet")
            continue
        kit = REPO / "kits" / category
        shutil.rmtree(kit, ignore_errors=True)
        (kit / "dataset").mkdir(parents=True)
        shutil.copy2(NOTEBOOK, kit / "member_collection.ipynb")
        shutil.copy2(ds, kit / "dataset" / "dataset.json")
        (kit / "README_MEMBER.txt").write_text(
            README.format(code=code, category=category), encoding="utf-8"
        )
        built.append((code, category, kit))
        print(f"built kit: {kit.relative_to(REPO)} ({code}, dataset {ds.stat().st_size} bytes)")

    if built:
        print("\nZip each kit folder and send it to the assigned member:")
        for code, category, kit in built:
            print(f"  (cd kits && zip -r ../../inbox_out/{code}_kit.zip {category})")
    else:
        print("No kits built (no category datasets collected yet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
