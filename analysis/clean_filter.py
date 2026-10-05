#!/usr/bin/env python3
"""Shared clean-corpus filter: collection artifacts excluded from the paper.

Exclusion set lives in results/final/excluded_units.json
(entries look like "category|task_id|model|condition"), produced by
analysis/clean_corpus.py. Import this from any analysis/plot script:

    from clean_filter import excluded, is_excluded
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def excluded():
    p = REPO / "results" / "final" / "excluded_units.json"
    if not p.is_file():
        return set()
    return set(json.loads(p.read_text()))


def is_excluded(category, task_id, model, condition, _cache=None):
    if _cache is None:
        _cache = excluded()
    return "|".join((category, task_id, model, condition)) in _cache
