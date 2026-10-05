import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- Config ----------
CSV_PATH = None                      # e.g. "students.csv"; None = use sample data
SUBJECTS = ["math", "science", "english"]
WEIGHTS = {"math": 1, "science": 1, "english": 1}   # e.g. {"math": 2, "science": 1.5, "english": 1}
SCORE_RANGE = (0, 100)
OPTIONAL_RANGES = {"attendance": (0, 100), "study_hours": (0, 24)}
PASS_MARK = 40
MIN_ROWS = 3
TOP_N = 10                           # leaderboard size

# ---------- 1. Load ----------
def load_data(path):
    if path is None:
        rng = np.random.default_rng(42)
        n = 60
        study = rng.uniform(1, 10, n).round(1)
        d = pd.DataFrame({
            "name": [f"Student_{i+1}" for i in range(n)],
            "study_hours": study,
            "attendance": rng.uniform(60, 100, n).round(1),
            "math": np.clip(40 + study * 4 + rng.normal(0, 8, n), 0, 100).round(1),
            "science": np.clip(35 + study * 4.5 + rng.normal(0, 9, n), 0, 100).round(1),
            "english": np.clip(50 + study * 3 + rng.normal(0, 7, n), 0, 100).round(1),
        })
        # Deliberately dirty rows to demonstrate validation
        d.loc[3, "math"] = 150
        d.loc[7, "science"] = "abc"
        d.loc[10, "name"] = ""
        d.loc[12, "english"] = np.nan
        d.loc[15, "attendance"] = 130
        d.loc[20, "name"] = d.loc[19, "name"]
        # Deliberate tie to demonstrate tie handling
        d.loc[30, SUBJECTS] = d.loc[31, SUBJECTS].values
        return d
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        sys.exit(f"ERROR: file not found: {path}")
    except pd.errors.EmptyDataError:
        sys.exit("ERROR: CSV is empty.")
    except Exception as e:
        sys.exit(f"ERROR: could not read CSV ({e})")

raw = load_data(CSV_PATH)
raw.columns = raw.columns.astype(str).str.strip().str.lower()
if raw.empty:
    sys.exit("ERROR: no rows in input.")

# ---------- 2. Schema validation ----------
missing_cols = [c for c in ["name"] + SUBJECTS if c not in raw.columns]
if missing_cols:
    sys.exit(f"ERROR: missing required column(s): {missing_cols}. Found: {list(raw.columns)}")

bad_weights = [s for s in SUBJECTS if s not in WEIGHTS or WEIGHTS[s] <= 0]
if bad_weights:
    sys.exit(f"ERROR: WEIGHTS must be positive numbers for every subject. Problem: {bad_weights}")

optional = [c for c in OPTIONAL_RANGES if c in raw.columns]
df = raw[["name"] + SUBJECTS + optional].copy()
df["row_id"] = df.index + 2          # spreadsheet-style row number (header = row 1)

# ---------- 3. Row-level validation ----------
issues = pd.DataFrame(index=df.index)

df["name"] = df["name"].astype("string").str.strip()
issues["missing_name"] = df["name"].isna() | (df["name"] == "")

for col in SUBJECTS + optional:
    original = df[col].copy()
    df[col] = pd.to_numeric(df[col], errors="coerce")
    issues[f"non_numeric_{col}"] = original.notna() & df[col].isna() & \
                                   (original.astype(str).str.strip() != "")

for col in SUBJECTS:
    issues[f"missing_{col}"] = df[col].isna() & ~issues[f"non_numeric_{col}"]
    issues[f"out_of_range_{col}"] = df[col].notna() & ~df[col].between(*SCORE_RANGE)

optional_warnings = {}
for col in optional:
    lo, hi = OPTIONAL_RANGES[col]
    bad = df[col].notna() & ~df[col].between(lo, hi)
    optional_warnings[col] = int(bad.sum() + issues[f"non_numeric_{col}"].sum())
    df.loc[bad, col] = np.nan

issues["duplicate_name"] = df["name"].duplicated(keep="first") & ~issues["missing_name"]

reject_cols = [c for c in issues.columns
               if not any(c == f"non_numeric_{o}" for o in optional)]
reject_mask = issues[reject_cols].any(axis=1)

rejected = df[reject_mask].copy()
rejected["reasons"] = issues.loc[reject_mask, reject_cols].apply(
    lambda r: ", ".join(r.index[r]), axis=1)
df = df[~reject_mask].drop(columns="row_id").reset_index(drop=True)

# ---------- 4. Validation report ----------
print("=== Validation Report ===")
print(f"Rows read:     {len(raw)}")
print(f"Rows accepted: {len(df)}")
print(f"Rows rejected: {len(rejected)}")
if not rejected.empty:
    print(rejected[["row_id", "name", "reasons"]].to_string(index=False))
    rejected.to_csv("rejected_rows.csv", index=False)
    print("Rejected rows saved to rejected_rows.csv")
for col, cnt in optional_warnings.items():
    if cnt:
        print(f"Warning: {cnt} invalid '{col}' value(s) set to missing (rows kept).")

if len(df) < MIN_ROWS:
    sys.exit(f"ERROR: only {len(df)} valid row(s); need at least {MIN_ROWS} for analysis.")

# ---------- 5. Metrics ----------
w = pd.Series(WEIGHTS)[SUBJECTS]
df["average"] = ((df[SUBJECTS] * w).sum(axis=1) / w.sum()).round(2)

def grade(s):
    return ("A" if s >= 85 else "B" if s >= 70 else
            "C" if s >= 55 else "D" if s >= PASS_MARK else "F")

df["grade"] = df["average"].apply(grade)
df["status"] = np.where(df[SUBJECTS].min(axis=1) < PASS_MARK, "At Risk", "OK")

# ---------- 6. Ranking ----------
n = len(df)

# 6a. Competition rank: tied averages share a rank (1, 2, 2, 4 ...)
df["rank"] = df["average"].rank(ascending=False, method="min").astype(int)
# 6b. Dense rank: no gaps after ties (1, 2, 2, 3 ...)
df["dense_rank"] = df["average"].rank(ascending=False, method="dense").astype(int)

# 6c. Unique position with tie-breakers:
#     higher average > higher lowest-subject score > name (A-Z)
order = (df.assign(min_score=df[SUBJECTS].min(axis=1))
           .sort_values(["average", "min_score", "name"], ascending=[False, False, True])
           .index)
df["position"] = pd.Series(np.arange(1, n + 1), index=order)

# 6d. Percentile and tier
df["percentile"] = ((n - df["rank"]) / (n - 1) * 100).round(1)
df["tier"] = pd.cut(df["percentile"], bins=[-0.1, 25, 50, 75, 100.1],
                    labels=["Bottom 25%", "Lower-mid", "Upper-mid", "Top 25%"])

# 6e. Per-subject ranks, plus strongest/weakest subject by rank
for s in SUBJECTS:
    df[f"{s}_rank"] = df[s].rank(ascending=False, method="min").astype(int)
rank_cols = [f"{s}_rank" for s in SUBJECTS]
df["strongest"] = df[rank_cols].idxmin(axis=1).str.replace("_rank", "", regex=False)
df["weakest"] = df[rank_cols].idxmax(axis=1).str.replace("_rank", "", regex=False)

# 6f. Gap to the student directly above
by_pos = df.sort_values("position")
df["gap_to_above"] = (by_pos["average"].shift(1) - by_pos["average"]).reindex(df.index).round(2)

df = df.sort_values("position").reset_index(drop=True)

# ---------- 7. Ranking reports ----------
print(f"\n=== Leaderboard (Top {min(TOP_N, n)}) ===")
print(df.head(TOP_N)[["position", "rank", "name", "average", "grade", "percentile", "strongest"]]
      .to_string(index=False))

print("\n=== Subject Toppers ===")
for s in SUBJECTS:
    best = df[s].max()
    names = ", ".join(df.loc[df[s] == best, "name"].astype(str))
    print(f"{s.title():8s} {best:6.1f}  ->  {names}")

ties = df[df.duplicated("rank", keep=False)].sort_values("rank")
print("\n=== Ties (share the same rank) ===")
print(ties[["rank", "position", "name", "average"]].to_string(index=False) if not ties.empty else "None")

print("\n=== Bottom 5 ===")
print(df.tail(5)[["position", "rank", "name", "average", "grade", "weakest"]].to_string(index=False))

print("\n=== Tier Counts ===")
print(df["tier"].value_counts().reindex(["Top 25%", "Upper-mid", "Lower-mid", "Bottom 25%"]))

# ---------- 8. Summary ----------
print("\n=== Subject Statistics ===")
print(df[SUBJECTS + ["average"]].describe().round(2).loc[["mean", "std", "min", "50%", "max"]])

print("\n=== Grade Distribution ===")
print(df["grade"].value_counts().reindex(list("ABCDF"), fill_value=0))

print(f"\n=== Pass Rate per Subject (>= {PASS_MARK}) ===")
print((df[SUBJECTS] >= PASS_MARK).mean().mul(100).round(1).astype(str) + "%")

print("\n=== At-Risk Students ===")
risk = df[df["status"] == "At Risk"]
print(risk[["position", "name"] + SUBJECTS].to_string(index=False) if not risk.empty else "None")

# ---------- 9. Correlations ----------
def usable(col):
    s = df[col].dropna()
    return len(s) >= MIN_ROWS and s.std() > 0

factors = [c for c in optional if usable(c)]
skipped = [c for c in optional if c not in factors]
if skipped:
    print(f"\nNote: skipped {skipped} in correlations (too few valid values or no variation).")

corr = df[factors + SUBJECTS + ["average"]].corr().round(2)
print("\n=== Correlation with Average ===")
print(corr["average"].drop("average"))

# ---------- 10. Visualizations ----------
fig, axes = plt.subplots(2, 3, figsize=(18, 9))
fig.suptitle("Student Performance & Ranking", fontsize=15, fontweight="bold")

for s in SUBJECTS:
    axes[0, 0].hist(df[s], bins=min(12, max(3, n // 3)), alpha=0.5, label=s.title())
axes[0, 0].set(title="Score Distribution", xlabel="Score", ylabel="Students")
axes[0, 0].legend()

grades = df["grade"].value_counts().reindex(list("ABCDF"), fill_value=0)
axes[0, 1].bar(grades.index, grades.values, color="steelblue")
axes[0, 1].set(title="Grade Distribution", xlabel="Grade", ylabel="Students")

# Top-N leaderboard
top = df.head(TOP_N).iloc[::-1]
axes[0, 2].barh(top["name"].astype(str), top["average"], color="seagreen")
axes[0, 2].set(title=f"Top {len(top)} Students", xlabel="Weighted average")
axes[0, 2].set_xlim(max(0, top["average"].min() - 10), 100)

if "study_hours" in factors:
    sub = df[["study_hours", "average"]].dropna()
    m, b = np.polyfit(sub["study_hours"], sub["average"], 1)
    xs = np.sort(sub["study_hours"].to_numpy())
    axes[1, 0].scatter(sub["study_hours"], sub["average"], alpha=0.7)
    axes[1, 0].plot(xs, m * xs + b, color="red")
    axes[1, 0].set(title="Study Hours vs Average", xlabel="Study hours/day", ylabel="Average score")
else:
    axes[1, 0].text(0.5, 0.5, "study_hours unavailable", ha="center", va="center")
    axes[1, 0].set_axis_off()

im = axes[1, 1].imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
axes[1, 1].set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
axes[1, 1].set_yticks(range(len(corr)), corr.columns)
axes[1, 1].set_title("Correlation Matrix")
fig.colorbar(im, ax=axes[1, 1])

# Strongest vs weakest subject counts
sw = pd.DataFrame({
    "Strongest": df["strongest"].value_counts().reindex(SUBJECTS, fill_value=0),
    "Weakest": df["weakest"].value_counts().reindex(SUBJECTS, fill_value=0),
})
sw.index = [s.title() for s in sw.index]
sw.plot.bar(ax=axes[1, 2], color=["seagreen", "indianred"], rot=0)
axes[1, 2].set(title="Strongest vs Weakest Subject", ylabel="Students")

plt.tight_layout()
plt.savefig("student_analysis.png", dpi=150)
plt.show()

# ---------- 11. Export ----------
export_cols = (["position", "rank", "dense_rank", "name"] + SUBJECTS +
               ["average", "grade", "percentile", "tier"] + rank_cols +
               ["strongest", "weakest", "gap_to_above", "status"] + optional)
df[export_cols].to_csv("student_analysis_results.csv", index=False)
print("\nSaved: student_analysis.png, student_analysis_results.csv")