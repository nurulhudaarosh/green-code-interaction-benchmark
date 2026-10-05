#!/usr/bin/env python3
"""Static code metrics + time-complexity estimator for every final program.

Reads:
  collected/<cat>/code/<model>/<task>/<cond>/{code.py|final.py}
  dataset/<cat>/dataset.json          (declared complexity per task)
  results/energy_runs.jsonl           (dynamic: runtime, energy, memory)
  inputs/<cat>/<task>/                (input bytes for energy/kg metrics)

Writes:
  results/final/code_metrics.csv          per-program metrics
  results/final/complexity_summary.json   aggregate summaries
"""
import ast
import csv
import hashlib
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLLECTED = REPO / "collected"
DATASET = REPO / "dataset"
INPUTS = REPO / "inputs"
LEDGER = REPO / "results" / "energy_runs.jsonl"
FINAL = REPO / "results" / "final"

STDLIB = set(getattr(sys, "stdlib_module_names", set()))

# ordinal rank used for correlations
COMPLEXITY_RANK = {
    "O(1)": 0,
    "O(log n)": 0.5,
    "O(n log n)": 1.5,
    "O(n)": 1,
    "O(n^2)": 2,
    "O(n^2 log n)": 2.5,
    "O(n^3)": 3,
    "O(2^n)": 5,
    "O(recursive)": 2.5,
    "unknown": -1,
}


class _Analyzer(ast.NodeVisitor):
    """Collect structural facts from a module AST."""

    def __init__(self):
        self.max_loop_depth = 0
        self.loop_depth = 0
        self.loops = 0
        self.whiles = 0
        self.branches = 0
        self.trys = 0
        self.comprehensions = 0
        self.if_exprs = 0
        self.bool_ops = 0
        self.match_cases = 0
        self.functions = 0
        self.classes = 0
        self.lambdas = 0
        self.async_defs = 0
        self.awaits = 0
        self.sorts = 0
        self.has_recursion = False
        self.func_stack = []
        self.calls_in_func = defaultdict(set)
        self.uses_stdin = False
        self.uses_argparse = False
        self.use_opens = 0
        self.has_main_guard = False
        self.imports = set()
        self.dynamic_exec = False

    # --- loops ---
    def visit_For(self, node):
        self._loop(node)

    def visit_AsyncFor(self, node):
        self._loop(node)

    def visit_While(self, node):
        self.loops += 1
        self.whiles += 1
        self._loop_body(node)

    def _loop(self, node):
        self.loops += 1
        self._loop_body(node)

    def _loop_body(self, node):
        self.loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self.loop_depth)
        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_If(self, node):
        if _is_main_guard(node):
            self.has_main_guard = True
        self.branches += 1
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.if_exprs += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.bool_ops += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_Try(self, node):
        self.trys += 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.comprehensions += 1 + len(node.ifs)
        self.generic_visit(node)

    def visit_Match(self, node):
        self.match_cases += max(0, len(node.cases) - 1)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions += 1
        self._enter_func(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions += 1
        self.async_defs += 1
        self._enter_func(node)

    def _enter_func(self, node):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_ClassDef(self, node):
        self.classes += 1
        self.generic_visit(node)

    def visit_Lambda(self, node):
        self.lambdas += 1
        self.generic_visit(node)

    def visit_Await(self, node):
        self.awaits += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        name = _call_name(node.func)
        if name == "sorted" or name.endswith(".sort") or name in ("heapify", "nlargest", "nsmallest"):
            self.sorts += 1
        if name == "input":
            self.uses_stdin = True
        if name == "open":
            self.use_opens += 1
        if name in ("eval", "exec", "compile", "__import__"):
            self.dynamic_exec = True
        if self.func_stack and name == self.func_stack[-1]:
            self.has_recursion = True
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # sys.stdin / argparse usage
        if isinstance(node.value, ast.Name):
            if node.value.id == "sys" and node.attr in ("stdin",):
                self.uses_stdin = True
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            self.imports.add(a.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def _call_name(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = _call_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    return ""


def _is_main_guard(node):
    test = node.test
    if isinstance(test, ast.Compare) and isinstance(test.left, ast.Name):
        if test.left.id == "__name__":
            return True
    return False


def _cyclomatic(tree):
    m = 1
    for n in ast.walk(tree):
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While,
                          ast.ExceptHandler, ast.IfExp)):
            m += 1
        elif isinstance(n, ast.BoolOp):
            m += max(0, len(n.values) - 1)
        elif isinstance(n, ast.comprehension):
            m += 1 + len(n.ifs)
        elif isinstance(n, ast.Match):
            m += max(0, len(n.cases) - 1)
    return m


def estimate_complexity(a: _Analyzer):
    """Heuristic Big-O class from structural facts. Documented in the paper."""
    if a.has_recursion and a.max_loop_depth >= 1:
        return "O(2^n)"          # backtracking / recursive search
    if a.has_recursion:
        return "O(recursive)"
    if a.max_loop_depth >= 4:
        return "O(n^4)"
    if a.max_loop_depth == 3:
        return "O(n^3)"
    if a.max_loop_depth == 2:
        return "O(n^2 log n)" if a.sorts else "O(n^2)"
    if a.max_loop_depth == 1:
        return "O(n log n)" if a.sorts else "O(n)"
    return "O(n log n)" if a.sorts else "O(1)"


def analyze_source(text):
    lines = text.splitlines()
    blank = sum(1 for ln in lines if not ln.strip())
    comment = sum(1 for ln in lines if ln.strip().startswith("#"))
    sloc = len(lines) - blank - comment
    m = {
        "parse_ok": 0, "loc_total": len(lines), "sloc": sloc,
        "loc_blank": blank, "loc_comment": comment,
        "functions": 0, "classes": 0, "lambdas": 0,
        "loops": 0, "while_loops": 0, "max_loop_depth": 0,
        "branches": 0, "try_blocks": 0, "comprehensions": 0,
        "if_exprs": 0, "bool_ops": 0, "match_cases": 0,
        "sorts": 0, "recursion": 0, "cyclomatic": 0,
        "imports": 0, "nonstdlib_imports": 0,
        "uses_stdin": 0, "uses_argparse": 0, "file_opens": 0,
        "has_main_guard": 0, "dynamic_exec": 0,
        "estimated_complexity": "unparseable", "complexity_rank": -1,
    }
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return m
    a = _Analyzer()
    a.visit(tree)
    m.update({
        "parse_ok": 1,
        "functions": a.functions, "classes": a.classes, "lambdas": a.lambdas,
        "loops": a.loops, "while_loops": a.whiles,
        "max_loop_depth": a.max_loop_depth, "branches": a.branches,
        "try_blocks": a.trys, "comprehensions": a.comprehensions,
        "if_exprs": a.if_exprs, "bool_ops": a.bool_ops,
        "match_cases": a.match_cases, "sorts": a.sorts,
        "recursion": int(a.has_recursion), "cyclomatic": _cyclomatic(tree),
        "imports": len(a.imports),
        "nonstdlib_imports": len(a.imports - STDLIB),
        "uses_stdin": int(a.uses_stdin or "argparse" in a.imports),
        "uses_argparse": int("argparse" in a.imports),
        "file_opens": a.use_opens, "has_main_guard": int(a.has_main_guard),
        "dynamic_exec": int(a.dynamic_exec),
    })
    est = estimate_complexity(a)
    m["estimated_complexity"] = est
    m["complexity_rank"] = COMPLEXITY_RANK.get(est, -1)
    return m


def final_program(cond_dir, cond):
    if cond == "ONE_SHOT":
        c = cond_dir / "code.py"
        if c.is_file():
            return c
    c = cond_dir / "final.py"
    if c.is_file():
        return c
    pys = sorted(f for f in cond_dir.glob("*.py") if f.name.startswith(("code", "final")))
    return pys[0] if pys else None


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_dynamic():
    dyn = {}
    if LEDGER.is_file():
        for line in LEDGER.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("status") == "ok":
                dyn[r["sha256"]] = r
    return dyn


def load_declared():
    """(category, task_id) -> declared complexity string."""
    out = {}
    for ds in DATASET.glob("*/dataset.json"):
        cat = ds.parent.name
        try:
            data = json.loads(ds.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for t in data.get("tasks", []):
            prof = t.get("computational_profile") or {}
            comp = None
            if isinstance(prof, dict):
                comp = prof.get("complexity")
            elif isinstance(prof, str):
                comp = prof
            if not comp:
                cons = t.get("constraints")
                if isinstance(cons, dict):
                    comp = cons.get("complexity_target")
            out[(cat, str(t.get("task_id")))] = comp or ""
    return out


def input_bytes(cat, task):
    d = INPUTS / cat / task
    if not d.is_dir():
        return 0
    total = 0
    for f in d.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total


def main():
    dyn = load_dynamic()
    declared = load_declared()
    rows = []
    for cat_dir in sorted(COLLECTED.iterdir()):
        code_root = cat_dir / "code"
        if not code_root.is_dir():
            continue
        cat = cat_dir.name
        for model_dir in sorted(code_root.iterdir()):
            for task_dir in sorted(model_dir.iterdir()):
                task = task_dir.name
                ibytes = input_bytes(cat, task)
                decl = declared.get((cat, task), "")
                for cond_dir in sorted(task_dir.iterdir()):
                    if not cond_dir.is_dir():
                        continue
                    prog = final_program(cond_dir, cond_dir.name)
                    if prog is None:
                        continue
                    text = prog.read_text(encoding="utf-8", errors="replace")
                    m = analyze_source(text)
                    sha = sha256(prog)
                    d = dyn.get(sha, {})
                    energy = d.get("energy_pkg_j")
                    runtime = d.get("runtime_s")
                    row = {
                        "category": cat, "task_id": task,
                        "model": model_dir.name, "condition": cond_dir.name,
                        "sha256": sha, "file": str(prog.relative_to(REPO)),
                        "status": d.get("status", "unmeasured"),
                        "declared_complexity": decl,
                        "declared_rank": COMPLEXITY_RANK.get(_norm(decl), -1),
                    }
                    row.update(m)
                    row["input_bytes"] = ibytes
                    row["runtime_s"] = runtime
                    row["energy_pkg_j"] = energy
                    row["energy_core_j"] = d.get("energy_core_j")
                    row["peak_mem_mb"] = d.get("peak_mem_mb")
                    row["power_w"] = (round(energy / runtime, 4)
                                      if energy and runtime else None)
                    row["energy_per_sloc"] = (round(energy / m["sloc"], 6)
                                              if energy and m["sloc"] else None)
                    row["energy_per_kb_input"] = (round(energy / (ibytes / 1024.0), 6)
                                                  if energy and ibytes else None)
                    row["complexity_compliant"] = _compliant(m, decl)
                    rows.append(row)

    FINAL.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys()) if rows else []
    with (FINAL / "code_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    summary = summarize(rows)
    (FINAL / "complexity_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[code_metrics] {len(rows)} programs "
          f"({sum(r['parse_ok'] for r in rows)} parseable) -> "
          f"{(FINAL / 'code_metrics.csv').relative_to(REPO)}")
    return 0


def _norm(decl):
    if not decl:
        return "unknown"
    d = decl.replace("²", "^2").replace("³", "^3").replace(" ", "").lower()
    if d.startswith("o(nlogn)") or "nlogn" in d:
        return "O(n log n)"
    if "2^n" in d or "2n" in d:
        return "O(2^n)"
    if "n^3" in d or "n³" in d:
        return "O(n^3)"
    if "n^2" in d or "n²" in d or "nm" in d or "rc" in d or "nq" in d or "nt" in d:
        return "O(n^2)"
    if d.startswith("o(n)") or "o(n" in d and "log" not in d:
        return "O(n)"
    if d.startswith("o(1)"):
        return "O(1)"
    return "other"


def _compliant(m, decl):
    if not m["parse_ok"]:
        return ""
    target = _norm(decl)
    rank = m["complexity_rank"]
    if target == "O(1)":
        return int(rank <= 0)
    if target == "O(n log n)":
        return int(rank <= 1.5)
    if target == "O(n)":
        return int(rank <= 1.5)
    if target == "O(n^2)":
        return int(rank <= 2.5)
    if target == "O(n^3)":
        return int(rank <= 3)
    if target == "O(2^n)":
        return int(rank <= 5)
    return ""


def _med(vals):
    vals = [v for v in vals if v is not None]
    return round(st.median(vals), 4) if vals else None


def summarize(rows):
    out = {"n_programs": len(rows),
           "n_parseable": sum(r["parse_ok"] for r in rows),
           "n_measured": sum(1 for r in rows if r["status"] == "ok")}
    # complexity distribution
    dist = Counter(r["estimated_complexity"] for r in rows if r["parse_ok"])
    out["complexity_distribution"] = dict(dist.most_common())
    # by condition
    by_cond = {}
    conds = ["ONE_SHOT", "BUG_FIX", "FEATURE_ADDITION", "EDGE_CASE", "FULL_MULTI_TURN"]
    for c in conds:
        sub = [r for r in rows if r["condition"] == c]
        parsed = [r for r in sub if r["parse_ok"]]
        by_cond[c] = {
            "n": len(sub),
            "n_parseable": len(parsed),
            "median_sloc": _med([r["sloc"] for r in parsed]),
            "median_functions": _med([r["functions"] for r in parsed]),
            "median_loops": _med([r["loops"] for r in parsed]),
            "mean_max_loop_depth": round(st.mean([r["max_loop_depth"] for r in parsed]), 3) if parsed else None,
            "median_cyclomatic": _med([r["cyclomatic"] for r in parsed]),
            "median_complexity_rank": _med([r["complexity_rank"] for r in parsed]),
            "pct_recursive": round(100 * sum(r["recursion"] for r in parsed) / len(parsed), 1) if parsed else None,
            "pct_quadratic_plus": round(100 * sum(1 for r in parsed if r["complexity_rank"] >= 2) / len(parsed), 1) if parsed else None,
            "compliant_rate": round(100 * sum(r["complexity_compliant"] for r in parsed if r["complexity_compliant"] != "") / max(1, sum(1 for r in parsed if r["complexity_compliant"] != "")), 1),
        }
    out["by_condition"] = by_cond
    # by model
    by_model = {}
    for m in sorted({r["model"] for r in rows}):
        parsed = [r for r in rows if r["model"] == m and r["parse_ok"]]
        by_model[m] = {
            "n": len(parsed),
            "median_sloc": _med([r["sloc"] for r in parsed]),
            "median_cyclomatic": _med([r["cyclomatic"] for r in parsed]),
            "median_complexity_rank": _med([r["complexity_rank"] for r in parsed]),
            "pct_quadratic_plus": round(100 * sum(1 for r in parsed if r["complexity_rank"] >= 2) / len(parsed), 1) if parsed else None,
        }
    out["by_model"] = by_model
    # by category
    by_cat = {}
    for c in sorted({r["category"] for r in rows}):
        parsed = [r for r in rows if r["category"] == c and r["parse_ok"]]
        compl = [r for r in parsed if r["complexity_compliant"] != ""]
        by_cat[c] = {
            "n": len(parsed),
            "median_sloc": _med([r["sloc"] for r in parsed]),
            "median_complexity_rank": _med([r["complexity_rank"] for r in parsed]),
            "pct_quadratic_plus": round(100 * sum(1 for r in parsed if r["complexity_rank"] >= 2) / len(parsed), 1) if parsed else None,
            "declared_compliant_rate": round(100 * sum(r["complexity_compliant"] for r in compl) / len(compl), 1) if compl else None,
        }
    out["by_category"] = by_cat
    out["correlations"] = correlations(rows)
    return out


def correlations(rows):
    ok = [r for r in rows if r["status"] == "ok" and r["energy_pkg_j"] is not None
          and r["parse_ok"]]
    res = {}

    def corr(xs, ys):
        pairs = [(x, y) for x, y in zip(xs, ys)
                 if x is not None and y is not None]
        if len(pairs) < 10:
            return None
        try:
            from scipy.stats import spearmanr, pearsonr
            sx = [p[0] for p in pairs]
            sy = [p[1] for p in pairs]
            rho = spearmanr(sx, sy).statistic
            r = pearsonr(sx, sy)[0]
            return {"n": len(pairs), "spearman_rho": round(float(rho), 4),
                    "pearson_r": round(float(r), 4)}
        except Exception:
            return None

    res["sloc_vs_energy"] = corr([r["sloc"] for r in ok], [r["energy_pkg_j"] for r in ok])
    res["cyclomatic_vs_energy"] = corr([r["cyclomatic"] for r in ok], [r["energy_pkg_j"] for r in ok])
    res["complexity_rank_vs_energy"] = corr([r["complexity_rank"] for r in ok], [r["energy_pkg_j"] for r in ok])
    res["loop_depth_vs_energy"] = corr([r["max_loop_depth"] for r in ok], [r["energy_pkg_j"] for r in ok])
    res["cyclomatic_vs_runtime"] = corr([r["cyclomatic"] for r in ok], [r["runtime_s"] for r in ok])
    res["sloc_vs_runtime"] = corr([r["sloc"] for r in ok], [r["runtime_s"] for r in ok])
    res["runtime_vs_energy"] = corr([r["runtime_s"] for r in ok], [r["energy_pkg_j"] for r in ok])
    res["sloc_vs_peak_mem"] = corr([r["sloc"] for r in ok], [r["peak_mem_mb"] for r in ok])
    return res


if __name__ == "__main__":
    sys.exit(main())
