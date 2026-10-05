import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# ---------- Config ----------
CSV_PATH = None                      # e.g. "students.csv"; None = use sample data
SUBJECTS = ["math", "science", "english"]
WEIGHTS = {"math": 1, "science": 1, "english": 1}   # numbers only (not strings/bools), > 0
SCORE_RANGE = (0, 100)               # inclusive on both ends
OPTIONAL_RANGES = {"attendance": (0, 100), "study_hours": (0, 24)}
PASS_MARK = 40                       # a score equal to PASS_MARK passes
MIN_ROWS = 3                         # forced to be at least 2
TOP_N = 10
GRADE_CUTOFFS = [(85, "A"), (70, "B"), (55, "C"), (40, "D")]   # descending; else "F"

def fail(msg):
    sys.exit(f"ERROR: {msg}")

def is_number(x):
    return isinstance(x, (int, float, np.integer, np.floating)) and not isinstance(x, (bool, np.bool_))

def safe_write(frame, path):
    try:
        frame.to_csv(path, index=False)
        return True
    except (PermissionError, OSError) as e:
        print(f"Warning: could not write {path} ({e}). Is it open in another program?")
        return False

# ---------- 0. Config validation ----------
if not isinstance(SUBJECTS, (list, tuple)) or not SUBJECTS:
    fail("SUBJECTS must be a non-empty list.")
if not all(isinstance(s, str) and s.strip() for s in SUBJECTS):
    fail("SUBJECTS must contain non-empty strings.")
SUBJECTS = [s.strip().lower().replace(" ", "_") for s in SUBJECTS]
if len(set(SUBJECTS)) != len(SUBJECTS):
    fail("SUBJECTS contains duplicates.")
if "name" in SUBJECTS or "average" in SUBJECTS:
    fail("SUBJECTS cannot include reserved names 'name' or 'average'.")

# score range
if (not isinstance(SCORE_RANGE, (tuple, list)) or len(SCORE_RANGE) != 2
        or not all(is_number(v) and np.isfinite(v) for v in SCORE_RANGE)):
    fail("SCORE_RANGE must be (min, max) with two finite numbers.")
lo, hi = SCORE_RANGE
if lo >= hi:
    fail(f"SCORE_RANGE {SCORE_RANGE} is invalid (min must be below max).")

# pass mark and grade cutoffs must live inside the score range
if not is_number(PASS_MARK) or not (lo <= PASS_MARK <= hi):
    fail(f"PASS_MARK must be a number within SCORE_RANGE {SCORE_RANGE}.")
try:
    cut_vals = [c for c, _ in GRADE_CUTOFFS]
    if not all(is_number(c) and lo <= c <= hi for c in cut_vals):
        raise ValueError
    if any(a <= b for a, b in zip(cut_vals, cut_vals[1:])):
        raise ValueError
except (TypeError, ValueError):
    fail("GRADE_CUTOFFS must be [(cutoff, grade), ...] in strictly descending order, inside SCORE_RANGE.")

# optional ranges
for k, v in OPTIONAL_RANGES.items():
    if (not isinstance(v, (tuple, list)) or len(v) != 2 or
            not all(is_number(x) and np.isfinite(x) for x in v) or v[0] >= v[1]):
        fail(f"OPTIONAL_RANGES['{k}'] must be (min, max) with min < max.")

# MIN_ROWS / TOP_N
if not is_number(MIN_ROWS) or MIN_ROWS != int(MIN_ROWS):
    fail("MIN_ROWS must be an integer.")
MIN_ROWS = max(2, int(MIN_ROWS))
if not is_number(TOP_N) or TOP_N != int(TOP_N) or TOP_N < 1:
    fail("TOP_N must be a positive integer.")
TOP_N = int(TOP_N)

# weights: must be a dict, cover exactly the subjects, numeric, finite, > 0
if not isinstance(WEIGHTS, dict):
    fail("WEIGHTS must be a dict like {'math': 1, ...}.")
norm_weights = {str(k).strip().lower().replace(" ", "_"): v for k, v in WEIGHTS.items()}
if len(norm_weights) != len(WEIGHTS):
    fail("WEIGHTS has keys that collide after normalization (case/spaces).")
missing_w = [s for s in SUBJECTS if s not in norm_weights]
extra_w = [k for k in norm_weights if k not in SUBJECTS]
if missing_w:
    fail(f"WEIGHTS is missing subject(s): {missing_w}.")
if extra_w:
    fail(f"WEIGHTS has unknown subject(s): {extra_w} (typo? valid: {SUBJECTS}).")
bad_w = {s: norm_weights[s] for s in SUBJECTS
         if not is_number(norm_weights[s]) or not np.isfinite(norm_weights[s]) or norm_weights[s] <= 0}
if bad_w:
    fail(f"WEIGHTS must be finite numbers > 0 (no strings, booleans, NaN, inf). Problem: {bad_w}")
w = pd.Series({s: float(norm_weights[s]) for s in SUBJECTS})[SUBJECTS]

# ---------- 1. Load ----------
def load_data(path):
    if path is None:
        rng = np.random.default_rng(42)
        n = 70
        study = rng.uniform(1, 10, n).round(1)
        d = pd.DataFrame({
            "name": [f"Student_{i+1}" for i in range(n)],
            "study_hours": study,
            "attendance": rng.uniform(60, 100, n).round(1),
            "math": np.clip(40 + study * 4 + rng.normal(0, 8, n), 0, 100).round(1),
            "science": np.clip(35 + study * 4.5 + rng.normal(0, 9, n), 0, 100).round(1),
            "english": np.clip(50 + study * 3 + rng.normal(0, 7, n), 0, 100).round(1),
        }).astype({"math": object, "science": object, "english": object})
        # Invalid scores
        d.loc[3, "math"] = 150                       # above range
        d.loc[4, "math"] = -5                        # below range
        d.loc[7, "science"] = "abc"                  # non-numeric text
        d.loc[8, "english"] = "85%"                  # text with symbol
        d.loc[9, "science"] = True                   # boolean is not a score
        d.loc[12, "english"] = np.nan                # missing
        d.loc[49, "math"] = "inf"                    # non-finite
        d.loc[56, "math"] = "-inf"                   # non-finite
        d.loc[57, "science"] = "nan"                 # text 'nan'
        # Valid-but-awkward scores (must be accepted)
        d.loc[58, "math"] = " 77 "                   # padded text number
        d.loc[59, "math"] = "1e2"                    # scientific notation = 100
        # Other dirty rows
        d.loc[10, "name"] = ""
        d.loc[15, "attendance"] = 130                # optional out of range (row kept)
        d.loc[20, "name"] = d.loc[19, "name"]        # duplicate name
        d.loc[30, SUBJECTS] = d.loc[31, SUBJECTS].values   # tie
        d.loc[48, "name"] = "  STUDENT_1 "           # duplicate ignoring case/spaces
        # Regression: invalid FIRST occurrence must not cause the valid later row to be rejected
        d.loc[60, "name"] = "Dup_Check"; d.loc[60, "math"] = 999       # invalid first
        d.loc[61, "name"] = "Dup_Check"                                # valid second -> kept
        d.loc[50, :] = np.nan                        # fully blank row
        d.loc[51, "name"] = "   "
        d.loc[52, "study_hours"] = -1
        d.loc[53, "attendance"] = 0
        d.loc[54, "attendance"] = 100
        d.loc[55, "study_hours"] = 24
        for idx, (nm, val) in zip(range(40, 46), [("Boundary_100", 100), ("Boundary_0", 0),
                                                  ("Boundary_85", 85), ("Boundary_70", 70),
                                                  ("Boundary_55", 55), ("Boundary_40", 40)]):
            d.loc[idx, "name"] = nm
            d.loc[idx, SUBJECTS] = val
        return d
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, skip_blank_lines=False, dtype=str)
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            fail(f"file not found: {path}")
        except (IsADirectoryError, PermissionError):
            fail(f"cannot open '{path}' (is it a folder, or locked?).")
        except pd.errors.EmptyDataError:
            fail("CSV is empty (no header or data).")
        except pd.errors.ParserError as e:
            fail(f"CSV is malformed ({e}).")
        except Exception as e:
            fail(f"could not read CSV ({e}).")
    fail("could not decode CSV (tried UTF-8 and Latin-1).")

raw = load_data(CSV_PATH)
raw.columns = (raw.columns.astype(str).str.strip().str.lower()
               .str.replace(r"\s+", "_", regex=True))
if raw.columns.duplicated().any():
    fail(f"duplicate column names after normalization: {list(raw.columns[raw.columns.duplicated()])}")
if raw.empty:
    fail("file has a header but no data rows.")

# ---------- 2. Schema validation ----------
missing_cols = [c for c in ["name"] + SUBJECTS if c not in raw.columns]
if missing_cols:
    fail(f"missing required column(s): {missing_cols}. Found: {list(raw.columns)}")

optional = [c for c in OPTIONAL_RANGES if c in raw.columns]
raw["row_id"] = raw.index + 2        # spreadsheet-style row number (header = row 1)

blank = raw.drop(columns="row_id").replace(r"^\s*$", np.nan, regex=True).isna().all(axis=1)
n_blank = int(blank.sum())
df = raw.loc[~blank, ["row_id", "name"] + SUBJECTS + optional].copy()
if df.empty:
    fail("all rows are blank.")

# ---------- 3. Row-level validation ----------
def parse_numeric(series):
    """Strict numeric parse. Returns (values, invalid_type_mask).
    Blank -> missing (not invalid). Text, booleans and 'nan' strings -> invalid."""
    is_bool = series.map(lambda v: isinstance(v, (bool, np.bool_)))
    cleaned = series.map(lambda v: v.strip() if isinstance(v, str) else v).replace("", np.nan)
    num = pd.to_numeric(cleaned.mask(is_bool), errors="coerce").astype(float)
    invalid = (cleaned.notna() & num.isna()) | is_bool
    return num, invalid

issues = pd.DataFrame(index=df.index)

df["name"] = (df["name"].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True))
issues["missing_name"] = df["name"] == ""

invalid_optional = {}
for col in SUBJECTS + optional:
    df[col], invalid = parse_numeric(df[col])
    finite = np.isfinite(df[col])
    if col in SUBJECTS:
        issues[f"non_numeric_{col}"] = invalid
        issues[f"missing_{col}"] = df[col].isna() & ~invalid
        issues[f"non_finite_{col}"] = df[col].notna() & ~finite
        issues[f"out_of_range_{col}"] = finite & ~df[col].between(lo, hi)
    else:
        invalid_optional[col] = invalid

optional_warnings = {}
for col in optional:
    olo, ohi = OPTIONAL_RANGES[col]
    bad = (df[col].notna() & ~(np.isfinite(df[col]) & df[col].between(olo, ohi))) | invalid_optional[col]
    optional_warnings[col] = int(bad.sum())
    df.loc[bad, col] = np.nan

# Duplicates are judged only among rows that are otherwise valid, so an invalid
# first occurrence can no longer cause a good later row to be rejected.
other_bad = issues.any(axis=1)
key = df["name"].str.casefold()
dup = pd.Series(False, index=df.index)
eligible = key[~other_bad]
dup.loc[eligible.index] = eligible.duplicated(keep="first")
issues["duplicate_name"] = dup

reject_mask = issues.any(axis=1)

rejected = raw.loc[df.index[reject_mask]].copy()            # original, unmodified values
if not rejected.empty:
    rejected["reasons"] = issues.loc[reject_mask].apply(lambda r: ", ".join(r.index[r]), axis=1)
df = df[~reject_mask].drop(columns="row_id").reset_index(drop=True)

# ---------- 4. Validation report ----------
print("=== Validation Report ===")
print(f"Rows read:      {len(raw)}")
print(f"Blank skipped:  {n_blank}")
print(f"Rows accepted:  {len(df)}")
print(f"Rows rejected:  {len(rejected)}")
if not rejected.empty:
    reason_counts = issues.loc[reject_mask].sum().loc[lambda s: s > 0].sort_values(ascending=False)
    print("Rejection reasons:", ", ".join(f"{k}={v}" for k, v in reason_counts.items()))
    print(rejected[["row_id", "name", "reasons"]].to_string(index=False))
    if safe_write(rejected, "rejected_rows.csv"):
        print("Rejected rows (original values) saved to rejected_rows.csv")
elif os.path.exists("rejected_rows.csv"):
    try:
        os.remove("rejected_rows.csv")
    except OSError:
        pass
for col, cnt in optional_warnings.items():
    if cnt:
        print(f"Warning: {cnt} invalid '{col}' value(s) set to missing (rows kept).")

if len(df) < MIN_ROWS:
    fail(f"only {len(df)} valid row(s); need at least {MIN_ROWS} for analysis.")

# ---------- 5. Metrics ----------
n = len(df)
df["average"] = ((df[SUBJECTS] * w).sum(axis=1) / w.sum()).round(2)

def grade(score):
    for cutoff, g in GRADE_CUTOFFS:
        if score >= cutoff:
            return g
    return "F"

df["grade"] = df["average"].apply(grade)
df["status"] = np.where(df[SUBJECTS].min(axis=1) < PASS_MARK, "At Risk", "OK")

# ---------- 6. Ranking ----------
df["rank"] = df["average"].rank(ascending=False, method="min").astype(int)
df["dense_rank"] = df["average"].rank(ascending=False, method="dense").astype(int)

order = (df.assign(min_score=df[SUBJECTS].min(axis=1))
           .sort_values(["average", "min_score", "name"], ascending=[False, False, True])
           .index)
df["position"] = pd.Series(np.arange(1, n + 1), index=order)

df["percentile"] = ((n - df["rank"]) / (n - 1) * 100).round(1)
df["tier"] = pd.Categorical(
    np.select([df["percentile"] >= 75, df["percentile"] >= 50, df["percentile"] >= 25],
              ["Top 25%", "Upper-mid", "Lower-mid"], default="Bottom 25%"),
    categories=["Top 25%", "Upper-mid", "Lower-mid", "Bottom 25%"], ordered=True)

for s in SUBJECTS:
    df[f"{s}_rank"] = df[s].rank(ascending=False, method="min").astype(int)
rank_cols = [f"{s}_rank" for s in SUBJECTS]
balanced = df[rank_cols].nunique(axis=1) == 1
df["strongest"] = df[rank_cols].idxmin(axis=1).str.replace("_rank", "", regex=False)
df["weakest"] = df[rank_cols].idxmax(axis=1).str.replace("_rank", "", regex=False)
df.loc[balanced, ["strongest", "weakest"]] = "balanced"

by_pos = df.sort_values("position")
df["gap_to_above"] = (by_pos["average"].shift(1) - by_pos["average"]).reindex(df.index).round(2)
df = df.sort_values("position").reset_index(drop=True)

top_n = min(TOP_N, n)
bottom_n = min(5, n)

# ---------- 7. Ranking reports ----------
print(f"\n=== Leaderboard (Top {top_n}) ===")
print(df.head(top_n)[["position", "rank", "name", "average", "grade", "percentile", "strongest"]]
      .to_string(index=False))

print("\n=== Subject Toppers ===")
for s in SUBJECTS:
    best = df[s].max()
    print(f"{s.title():8s} {best:6.1f}  ->  {', '.join(df.loc[df[s] == best, 'name'])}")

ties = df[df.duplicated("rank", keep=False)].sort_values("rank")
print("\n=== Ties (share the same rank) ===")
print(ties[["rank", "position", "name", "average"]].to_string(index=False) if not ties.empty else "None")

print(f"\n=== Bottom {bottom_n} ===")
print(df.tail(bottom_n)[["position", "rank", "name", "average", "grade", "weakest"]].to_string(index=False))

print("\n=== Tier Counts ===")
print(df["tier"].value_counts().sort_index())

# ---------- 8. Summary ----------
print("\n=== Subject Statistics ===")
print(df[SUBJECTS + ["average"]].describe().round(2).loc[["mean", "std", "min", "50%", "max"]])

print("\n=== Grade Distribution ===")
print(df["grade"].value_counts().reindex([g for _, g in GRADE_CUTOFFS] + ["F"], fill_value=0))

print(f"\n=== Pass Rate per Subject (>= {PASS_MARK}) ===")
print((df[SUBJECTS] >= PASS_MARK).mean().mul(100).round(1).astype(str) + "%")

print("\n=== At-Risk Students ===")
risk = df[df["status"] == "At Risk"]
print(risk[["position", "name"] + SUBJECTS].to_string(index=False) if not risk.empty else "None")

# ---------- 9. Correlations ----------
def varies(col):
    s = df[col].dropna()
    return len(s) >= MIN_ROWS and s.nunique() > 1

candidates = optional + SUBJECTS + ["average"]
varying = [c for c in candidates if varies(c)]
skipped = [c for c in candidates if c not in varying]
if skipped:
    print(f"\nNote: skipped {skipped} in correlations (too few valid values or no variation).")

corr = None
if "average" in varying and len(varying) >= 2:
    corr = df[varying].corr().round(2)
    print("\n=== Correlation with Average ===")
    print(corr["average"].drop("average"))
else:
    print("\nCorrelations unavailable: not enough variation in the data.")

# ---------- 10. Visualizations ----------
fig, axes = plt.subplots(2, 3, figsize=(18, 9))
fig.suptitle("Student Performance & Ranking", fontsize=15, fontweight="bold")

for s in SUBJECTS:
    axes[0, 0].hist(df[s], bins=min(12, max(3, n // 3)), alpha=0.5, label=s.title())
axes[0, 0].set(title="Score Distribution", xlabel="Score", ylabel="Students")
axes[0, 0].legend()

grade_labels = [g for _, g in GRADE_CUTOFFS] + ["F"]
grades = df["grade"].value_counts().reindex(grade_labels, fill_value=0)
axes[0, 1].bar(grades.index, grades.values, color="steelblue")
axes[0, 1].set(title="Grade Distribution", xlabel="Grade", ylabel="Students")

top = df.head(top_n).iloc[::-1]
axes[0, 2].barh(top["name"], top["average"], color="seagreen")
axes[0, 2].set(title=f"Top {len(top)} Students", xlabel="Weighted average")
axes[0, 2].set_xlim(max(lo, top["average"].min() - 10), hi)

if "study_hours" in varying:
    sub = df[["study_hours", "average"]].dropna()
    m, b = np.polyfit(sub["study_hours"], sub["average"], 1)
    xs = np.sort(sub["study_hours"].to_numpy())
    axes[1, 0].scatter(sub["study_hours"], sub["average"], alpha=0.7)
    axes[1, 0].plot(xs, m * xs + b, color="red")
    axes[1, 0].set(title="Study Hours vs Average", xlabel="Study hours/day", ylabel="Average score")
else:
    axes[1, 0].text(0.5, 0.5, "study_hours unavailable or constant", ha="center", va="center")
    axes[1, 0].set_axis_off()

if corr is not None:
    im = axes[1, 1].imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    axes[1, 1].set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    axes[1, 1].set_yticks(range(len(corr)), corr.columns)
    axes[1, 1].set_title("Correlation Matrix")
    fig.colorbar(im, ax=axes[1, 1])
else:
    axes[1, 1].text(0.5, 0.5, "correlations unavailable", ha="center", va="center")
    axes[1, 1].set_axis_off()

cats = SUBJECTS + ["balanced"]
sw = pd.DataFrame({
    "Strongest": df["strongest"].value_counts().reindex(cats, fill_value=0),
    "Weakest": df["weakest"].value_counts().reindex(cats, fill_value=0),
})
sw.index = [c.title() for c in sw.index]
sw.plot.bar(ax=axes[1, 2], color=["seagreen", "indianred"], rot=0)
axes[1, 2].set(title="Strongest vs Weakest Subject", ylabel="Students")

plt.tight_layout()
try:
    plt.savefig("student_analysis.png", dpi=150)
except (PermissionError, OSError) as e:
    print(f"Warning: could not save chart ({e}).")
if "agg" not in matplotlib.get_backend().lower():
    plt.show()
plt.close(fig)

# ---------- 11. Export ----------
export_cols = (["position", "rank", "dense_rank", "name"] + SUBJECTS +
               ["average", "grade", "percentile", "tier"] + rank_cols +
               ["strongest", "weakest", "gap_to_above", "status"] + optional)
if safe_write(df[export_cols], "student_analysis_results.csv"):
    print("\nSaved: student_analysis.png, student_analysis_results.csv")