# Collection (member workflow, no bot)

`member_collection.ipynb` is the single tool each team member runs in
Google Colab (or local Jupyter) to collect model responses for **one category**.

## Per-category flow

1. Coordinator builds the kit: `python3 scripts/make_member_kit.py SR`
   → `kits/search_retrieval/` (notebook + dataset + member instructions).
2. Member copies the kit folder to Google Drive as `Green-Code-Collection`,
   opens the notebook in Colab, and works through every
   task × model × interaction unit following the notebook prompts.
3. Member runs the notebook's final validation + export cells and sends back
   `.collection/submissions/collection_submission.zip`.
4. Coordinator drops all 6 ZIPs into `inbox/` and runs:

   ```bash
   python3 scripts/ingest_zips.py
   ```

   The script validates (expected files, non-empty, Python syntax, manifest
   hashes), merges into `collected/<category>/`, updates
   `dataset/<category>/dataset.json`, and writes `collected/STATUS.md`.

Validation depends only on the ZIP **folder structure**, not the notebook
version — members may customize prompts/instructions in their notebook copy.
Each ZIP's notebook is saved under `collected/<category>/notebook/` for
provenance, and expected file counts come from the dataset bundled inside
that ZIP.

## ZIP layout produced by the notebook

```
Green-Code-Collection/
├── member_collection.ipynb
├── dataset/dataset.json
└── .collection/
    ├── state.json
    ├── logs/{activity,errors}.jsonl
    ├── raw/<model>/<task>/<INTERACTION>/turn_XX.txt|.json
    ├── code/<model>/<task>/<INTERACTION>/*.py
    └── submissions/{manifest.json, collection_submission.zip}
```

## Code file naming (per notebook)

| Interaction | Files |
|---|---|
| ONE_SHOT | `code.py` |
| BUG_FIX / FEATURE_ADDITION / EDGE_CASE | `initial.py`, `final.py` |
| FULL_MULTI_TURN | `turn_01.py … turn_04.py`, `final.py` (= turn 4) |
