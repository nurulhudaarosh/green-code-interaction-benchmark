#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

METADATA_FILE="$ROOT_DIR/metadata.json"
DATASET_ROOT="$ROOT_DIR/dataset"

SUBMISSION_DIR="$ROOT_DIR/submission"
SUBMISSIONS_DIR="$ROOT_DIR/submissions"

MODELS=("gpt" "claude" "gemini" "deepseek")

# ============================================================
# Colors
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# ============================================================
# Environment
# ============================================================

check_environment() {

    [[ -f "$METADATA_FILE" ]] \
        || error "metadata.json not found."

    [[ -d "$DATASET_ROOT" ]] \
        || error "dataset/ directory not found."

    command -v python3 >/dev/null 2>&1 \
        || error "Python3 is required."

    command -v zip >/dev/null 2>&1 \
        || error "zip is required."
}

# ============================================================
# Read metadata
# ============================================================

read_metadata() {

    local output

    output="$(
        python3 - "$METADATA_FILE" <<'PY'
import json
import sys

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    print(f"ERROR:Invalid metadata.json: {e}", file=sys.stderr)
    sys.exit(1)

category = data.get("category")
task_id = data.get("task_id")
completed = data.get("completed", 0)

if not category:
    print("ERROR:Missing category", file=sys.stderr)
    sys.exit(1)

if not task_id:
    print("ERROR:Missing task_id", file=sys.stderr)
    sys.exit(1)

if not isinstance(completed, int):
    print("ERROR:completed must be integer", file=sys.stderr)
    sys.exit(1)

print(category)
print(task_id)
print(completed)
PY
    )" || error "Could not read metadata.json."

    mapfile -t META <<< "$output"

    CATEGORY="${META[0]}"
    TASK_ID="${META[1]}"
    COMPLETED="${META[2]}"
}

# ============================================================
# Find dataset
# ============================================================

find_dataset() {

    DATASET_FILE="$DATASET_ROOT/$CATEGORY/dataset.json"

    [[ -f "$DATASET_FILE" ]] \
        || error "Dataset not found: $DATASET_FILE"
}

# ============================================================
# Read current task
# ============================================================

read_task() {

    local task_json

    task_json="$(
        python3 - "$DATASET_FILE" "$TASK_ID" <<'PY'
import json
import sys

dataset_file = sys.argv[1]
task_id = sys.argv[2]

with open(dataset_file, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    tasks = data.get("tasks", [])
else:
    tasks = data

if not isinstance(tasks, list):
    print("ERROR:Invalid task list", file=sys.stderr)
    sys.exit(1)

task = None

for item in tasks:
    if item.get("task_id") == task_id:
        task = item
        break

if task is None:
    print(f"ERROR:Task {task_id} not found", file=sys.stderr)
    sys.exit(1)

result = {
    "task_id": task_id,
    "title": task.get("title", ""),
    "interactions": list(
        task.get("interaction_design", {}).keys()
    )
}

print(json.dumps(result))
PY
    )" || error "Could not find task $TASK_ID."

    TASK_TITLE="$(
        python3 - "$task_json" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])
print(data["title"])
PY
    )"

    mapfile -t INTERACTIONS < <(
        python3 - "$task_json" <<'PY'
import json
import sys

data = json.loads(sys.argv[1])

for interaction in data["interactions"]:
    print(interaction)
PY
    )

    [[ "${#INTERACTIONS[@]}" -gt 0 ]] \
        || error "No interaction_design found for $TASK_ID."
}

# ============================================================
# Create interaction files
# ============================================================

create_interaction() {

    local model="$1"
    local interaction="$2"

    local base="$SUBMISSION_DIR/$model"

    case "$interaction" in

        ONE_SHOT)

            mkdir -p "$base/one_shot"

            touch "$base/one_shot/code.py"
            ;;

        BUG_FIX)

            mkdir -p "$base/bug_fix"

            touch "$base/bug_fix/initial.py"
            touch "$base/bug_fix/final.py"
            ;;

        FEATURE_ADDITION)

            mkdir -p "$base/feature_addition"

            touch "$base/feature_addition/initial.py"
            touch "$base/feature_addition/final.py"
            ;;

        EDGE_CASE)

            mkdir -p "$base/edge_case"

            touch "$base/edge_case/initial.py"
            touch "$base/edge_case/final.py"
            ;;

        FULL_MULTI_TURN)

            mkdir -p "$base/full_multi_turn"

            touch "$base/full_multi_turn/turn_01.py"
            touch "$base/full_multi_turn/turn_02.py"
            touch "$base/full_multi_turn/turn_03.py"
            touch "$base/full_multi_turn/turn_04.py"
            touch "$base/full_multi_turn/final.py"
            ;;

        *)

            error "Unknown interaction: $interaction"
            ;;

    esac
}

# ============================================================
# Create submission template
# ============================================================

create_template() {

    rm -rf "$SUBMISSION_DIR"

    mkdir -p "$SUBMISSION_DIR"

    # ------------------------------
    # Submission metadata
    # ------------------------------

    cat > "$SUBMISSION_DIR/metadata.json" <<'SUBMISSION_METADATA'
{
  "category": "__CATEGORY__",
  "task_id": "__TASK_ID__"
}
SUBMISSION_METADATA

    sed -i \
        "s/__CATEGORY__/$CATEGORY/g; s/__TASK_ID__/$TASK_ID/g" \
        "$SUBMISSION_DIR/metadata.json"

    # ------------------------------
    # Create model folders
    # ------------------------------

    for model in "${MODELS[@]}"; do

        for interaction in "${INTERACTIONS[@]}"; do

            create_interaction "$model" "$interaction"

        done

    done

    # ------------------------------
    # README
    # ------------------------------

    cat > "$SUBMISSION_DIR/README.txt" <<'SUBMISSION_README'
GREEN CODE INTERACTION BENCHMARK
================================

Instructions:

1. Use the exact prompts provided in the dataset.

2. Do not rename any folder or file.

3. Do not modify metadata.json.

4. Complete all four models:
      - GPT
      - Claude
      - Gemini
      - DeepSeek

5. For multi-turn interactions, continue the
   SAME conversation with the same model.

6. Save each generated code version in the
   corresponding file.

7. final.py must contain the final generated code.

8. Do not add extra files.

9. When the task is complete, return to the
   project root and run:

       ./sc.sh submit

The script will validate the submission,
create the ZIP, remove the old template,
advance to the next task and create the
next submission template automatically.
SUBMISSION_README

    echo
    echo "=============================================="
    echo -e "${GREEN}✅ NEW TASK TEMPLATE CREATED${NC}"
    echo "=============================================="
    echo
    echo -e "${BOLD}Category:${NC} $CATEGORY"
    echo -e "${BOLD}Task ID :${NC} $TASK_ID"
    echo -e "${BOLD}Title   :${NC} $TASK_TITLE"
    echo
    echo -e "${BOLD}Interactions:${NC}"

    for interaction in "${INTERACTIONS[@]}"; do
        echo "  ✓ $interaction"
    done

    echo
    echo "Template:"
    echo "  submission/"
    echo
}

# ============================================================
# Validate submission
# ============================================================

validate_submission() {

    [[ -d "$SUBMISSION_DIR" ]] \
        || error "submission/ folder does not exist."

    [[ -f "$SUBMISSION_DIR/metadata.json" ]] \
        || error "submission/metadata.json is missing."

    # ------------------------------
    # Validate metadata
    # ------------------------------

    python3 \
        "$SUBMISSION_DIR/metadata.json" \
        "$CATEGORY" \
        "$TASK_ID" <<'PY' \
        || error "Submission metadata is invalid."

import json
import sys

metadata_file = sys.argv[1]
expected_category = sys.argv[2]
expected_task = sys.argv[3]

with open(metadata_file, "r", encoding="utf-8") as f:
    data = json.load(f)

if data.get("category") != expected_category:
    raise SystemExit("Category mismatch.")

if data.get("task_id") != expected_task:
    raise SystemExit("Task ID mismatch.")
PY

    # ------------------------------
    # Validate files
    # ------------------------------

    for model in "${MODELS[@]}"; do

        for interaction in "${INTERACTIONS[@]}"; do

            case "$interaction" in

                ONE_SHOT)

                    files=(
                        "$SUBMISSION_DIR/$model/one_shot/code.py"
                    )
                    ;;

                BUG_FIX)

                    files=(
                        "$SUBMISSION_DIR/$model/bug_fix/initial.py"
                        "$SUBMISSION_DIR/$model/bug_fix/final.py"
                    )
                    ;;

                FEATURE_ADDITION)

                    files=(
                        "$SUBMISSION_DIR/$model/feature_addition/initial.py"
                        "$SUBMISSION_DIR/$model/feature_addition/final.py"
                    )
                    ;;

                EDGE_CASE)

                    files=(
                        "$SUBMISSION_DIR/$model/edge_case/initial.py"
                        "$SUBMISSION_DIR/$model/edge_case/final.py"
                    )
                    ;;

                FULL_MULTI_TURN)

                    files=(
                        "$SUBMISSION_DIR/$model/full_multi_turn/turn_01.py"
                        "$SUBMISSION_DIR/$model/full_multi_turn/turn_02.py"
                        "$SUBMISSION_DIR/$model/full_multi_turn/turn_03.py"
                        "$SUBMISSION_DIR/$model/full_multi_turn/turn_04.py"
                        "$SUBMISSION_DIR/$model/full_multi_turn/final.py"
                    )
                    ;;

            esac

            for file in "${files[@]}"; do

                [[ -s "$file" ]] \
                    || error "Missing or empty file: $file"

            done

        done

    done

    success "Submission validation passed."
}

# ============================================================
# Advance to next task
# ============================================================

advance_task() {

    local next_task

    next_task="$(
        python3 \
            "$DATASET_FILE" \
            "$TASK_ID" \
            "$METADATA_FILE" <<'PY'
import json
import sys

dataset_file = sys.argv[1]
current_task = sys.argv[2]
metadata_file = sys.argv[3]

with open(dataset_file, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, dict):
    tasks = data.get("tasks", [])
else:
    tasks = data

task_ids = [
    task.get("task_id")
    for task in tasks
]

try:
    index = task_ids.index(current_task)
except ValueError:
    raise SystemExit("Current task not found.")

with open(metadata_file, "r", encoding="utf-8") as f:
    metadata = json.load(f)

metadata["completed"] = metadata.get("completed", 0) + 1

if index + 1 < len(task_ids):

    metadata["task_id"] = task_ids[index + 1]

    next_task = task_ids[index + 1]

else:

    metadata["task_id"] = None

    next_task = "LAST_TASK"

with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
    f.write("\n")

print(next_task)
PY
    )"

    echo "$next_task"
}

# ============================================================
# INIT
# ============================================================

init() {

    check_environment
    read_metadata
    find_dataset
    read_task

    create_template
}

# ============================================================
# SUBMIT
# ============================================================

submit() {

    check_environment
    read_metadata
    find_dataset
    read_task

    echo
    echo "=============================================="
    echo -e "${BOLD}SUBMITTING TASK${NC}"
    echo "=============================================="
    echo
    echo "Category : $CATEGORY"
    echo "Task ID  : $TASK_ID"
    echo "Title    : $TASK_TITLE"
    echo

    # ------------------------------
    # Validate
    # ------------------------------

    validate_submission

    # ------------------------------
    # Create archive directory
    # ------------------------------

    mkdir -p "$SUBMISSIONS_DIR"

    ARCHIVE="$SUBMISSIONS_DIR/${TASK_ID}.zip"

    rm -f "$ARCHIVE"

    # ------------------------------
    # Create ZIP
    # ------------------------------

    (
        cd "$ROOT_DIR"

        zip -qr "$ARCHIVE" submission
    )

    success "ZIP created:"
    echo "  $ARCHIVE"

    # ------------------------------
    # Remove current template
    # ------------------------------

    rm -rf "$SUBMISSION_DIR"

    success "Old submission template removed."

    # ------------------------------
    # Advance task
    # ------------------------------

    NEXT_TASK="$(advance_task)"

    if [[ "$NEXT_TASK" == "LAST_TASK" ]]; then

        echo
        warning "All tasks in this category are completed."

        return
    fi

    # ------------------------------
    # Create next template
    # ------------------------------

    read_metadata
    find_dataset
    read_task

    create_template

    echo
    success "Ready for next task: $TASK_ID"
}

# ============================================================
# STATUS
# ============================================================

status() {

    check_environment
    read_metadata
    find_dataset
    read_task

    echo
    echo "=============================================="
    echo "BENCHMARK STATUS"
    echo "=============================================="
    echo
    echo "Category  : $CATEGORY"
    echo "Task ID   : $TASK_ID"
    echo "Title     : $TASK_TITLE"
    echo "Completed : $COMPLETED"
    echo
    echo "Interactions:"

    for interaction in "${INTERACTIONS[@]}"; do
        echo "  ✓ $interaction"
    done

    echo
}

# ============================================================
# RESET
# ============================================================

reset_submission() {

    if [[ -d "$SUBMISSION_DIR" ]]; then

        rm -rf "$SUBMISSION_DIR"

        success "submission/ removed."

    else

        info "No submission/ folder exists."

    fi
}

# ============================================================
# MAIN
# ============================================================

case "${1:-}" in

    init)
        init
        ;;

    submit)
        submit
        ;;

    status)
        status
        ;;

    reset)
        reset_submission
        ;;

    *)

        echo
        echo "Green Code Interaction Benchmark"
        echo
        echo "Usage:"
        echo
        echo "  ./sc.sh init"
        echo "  ./sc.sh submit"
        echo "  ./sc.sh status"
        echo "  ./sc.sh reset"
        echo

        ;;

esac