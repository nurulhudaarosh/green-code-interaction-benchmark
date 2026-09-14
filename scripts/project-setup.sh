#!/usr/bin/env bash
# Scaffold/repair the project directory layout. Safe to re-run: it only
# creates missing directories and placeholder files, never overwrites
# real content (datasets are only stubbed when missing or empty).
set -e
cd "$(dirname "$0")/.."

echo "Setting up Green Code Interaction Benchmark... ($(pwd))"

mkdir -p dataset tests/harness results/raw results/processed results/final/plots
mkdir -p inbox collected collection config runner measurement analysis scripts

touch inbox/.gitkeep results/raw/.gitkeep results/processed/.gitkeep results/final/.gitkeep

# Valid placeholder datasets for categories not collected yet, so every
# tool in the pipeline can parse them (0-byte files are invalid JSON).
python3 - <<'EOF'
import json
from pathlib import Path

CATEGORIES = {
    "file_data_processing": "FD",
    "text_log_processing": "TL",
    "search_retrieval": "SR",
    "algorithms_computation": "AC",
    "image_media_processing": "IM",
    "realistic_applications_utilities": "RA",
}
for cat, code in CATEGORIES.items():
    f = Path("dataset") / cat / "dataset.json"
    if f.is_file() and f.stat().st_size > 0:
        continue
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({
        "dataset_metadata": {
            "category": cat, "category_code": code,
            "dataset_version": "pending",
            "status": "awaiting member collection",
        },
        "tasks": [],
    }, indent=2) + "\n", encoding="utf-8")
    print(f"stubbed {f}")
EOF

[ -f config/experiment.json ] || echo '{}' > config/experiment.json

cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
env/

# Environment
.env

# Generated submissions
submissions/
*.zip

# Member kit builds / incoming submissions
kits/
inbox/*
!inbox/.gitkeep

# Auto-materialized run inputs (regenerated per task/scale)
inputs/

# Generated experiment results
results/raw/*
results/processed/*
results/final/*
results/measurement_queue.jsonl

!results/raw/.gitkeep
!results/processed/.gitkeep
!results/final/.gitkeep

# Logs
*.log

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF

echo
echo "Project structure ready. Next steps:"
echo "  pip install -r requirements.txt"
echo "  python3 scripts/run_pipeline.py --no-sync   # full pass without Drive sync"
echo
find . -path ./.git -prune -o -maxdepth 2 -print | sort
