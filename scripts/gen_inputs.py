#!/usr/bin/env python3
"""Generate per-task inputs (code-driven) into inputs/<category>/<task_id>/.

Only tasks whose collected code actually reads stdin or opens files get
inputs; everything else gets nothing. Deterministic (seeded from task_id).
"""
import json
import random
from pathlib import Path

REPO = Path("/home/arosh/code/green-code-interaction-benchmark")
INPUTS = REPO / "inputs"
N_BIG = 4000


def seed_for(tid):
    return random.Random(sum(ord(c) for c in tid) & 0xFFFF)


def w_ints(rng, n, lo, hi):
    return [rng.randint(lo, hi) for _ in range(n)]


# ---------- algorithms_computation ----------

def gen_ac001(d):  # gpt style: n, then n lines "start end"
    rng = seed_for("AC-001")
    lines = [str(N_BIG)]
    for i in range(N_BIG):
        s = rng.randint(0, 10 ** 6)
        e = s + rng.randint(1, 1000)
        lines.append(f"{s} {e}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac003(d):  # dijkstra: n m, m lines u v w, last line s
    rng = seed_for("AC-003")
    n, m = 2000, N_BIG
    lines = [f"{n} {m}"]
    for _ in range(m):
        u, v = rng.randint(0, n - 1), rng.randint(0, n - 1)
        lines.append(f"{u} {v} {rng.randint(1, 100)}")
    lines.append("0")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac004(d):  # jobs: n, n lines start finish profit
    rng = seed_for("AC-004")
    lines = [str(N_BIG)]
    t = 0
    for _ in range(N_BIG):
        s = t
        t += rng.randint(1, 50)
        lines.append(f"{s} {t} {rng.randint(1, 500)}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac005(d):  # n, then n integers
    rng = seed_for("AC-005")
    vals = w_ints(rng, N_BIG, -10 ** 6, 10 ** 6)
    (d / "input.txt").write_text(f"{N_BIG}\n" + " ".join(map(str, vals)) + "\n")


def gen_ac006(d):  # rows cols T, grid values
    rng = seed_for("AC-006")
    rows = cols = 60
    grid = "\n".join(" ".join(str(rng.randint(0, 9)) for _ in range(cols))
                     for _ in range(rows))
    (d / "input.txt").write_text(f"{rows} {cols} 5\n{grid}\n")


def gen_ac007(d):  # MST: n m, m lines u v w
    rng = seed_for("AC-007")
    n, m = 2000, N_BIG
    lines = [f"{n} {m}"]
    for _ in range(m):
        lines.append(f"{rng.randint(0, n - 1)} {rng.randint(0, n - 1)} "
                     f"{rng.randint(1, 100)}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac008(d):  # fenwick: n q, n ints, q ops
    rng = seed_for("AC-008")
    n, q = N_BIG, N_BIG
    lines = [f"{n} {q}", " ".join(str(rng.randint(0, 10 ** 6)) for _ in range(n))]
    for _ in range(q):
        if rng.random() < 0.5:
            lines.append(f"update {rng.randint(0, n - 1)} {rng.randint(0, 10 ** 6)}")
        else:
            l = rng.randint(0, n - 1)
            r = min(n - 1, l + rng.randint(0, 500))
            lines.append(f"query {l} {r}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac010(d):  # matrix chain: one line of dims
    rng = seed_for("AC-010")
    dims = w_ints(rng, 40, 1, 100)
    (d / "input.txt").write_text(" ".join(map(str, dims)) + "\n")


def gen_ac013(d):  # 2D prefix: R C + R*C ints + Q rect queries
    rng = seed_for("AC-013")
    r = c = 60
    vals = " ".join(str(rng.randint(0, 100)) for _ in range(r * c))
    q = 3000
    lines = [f"{r} {c}", vals, str(q)]
    for _ in range(q):
        r1, c1 = rng.randint(0, r - 1), rng.randint(0, c - 1)
        r2 = min(r - 1, r1 + rng.randint(0, 30))
        c2 = min(c - 1, c1 + rng.randint(0, 30))
        lines.append(f"{r1} {c1} {r2} {c2}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_ac015(d):  # max-flow: n m s t, m lines u v cap
    rng = seed_for("AC-015")
    n, m = 1500, N_BIG
    lines = [f"{n} {m} 0 {n - 1}"]
    for _ in range(m):
        lines.append(f"{rng.randint(0, n - 1)} {rng.randint(0, n - 1)} "
                     f"{rng.randint(1, 100)}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


# ---------- file_data_processing ----------

def gen_fd001(d):  # events.csv for --input (claude/gpt); gemini self-contained
    rng = seed_for("FD-001")
    rows = ["customer_id,timestamp,status,amount"]
    statuses = ["completed", "pending", "failed", "refunded"]
    for i in range(N_BIG):
        ts = (f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28):02d}"
              f"T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00")
        rows.append(f"CUST{rng.randint(0, 800):05d},{ts},"
                    f"{statuses[i % 4]},{rng.randint(1, 5000)}")
    (d / "events.csv").write_text("\n".join(rows) + "\n")


def gen_fd002(d):  # NDJSON lines: user.id / request.endpoint,status,latency_ms
    rng = seed_for("FD-002")
    eps = ["/api/login", "/api/data", "/api/upload", "/api/search", "/api/logout"]
    lines = []
    for i in range(N_BIG):
        rec = {"user": {"id": rng.randint(1, 500), "name": f"user{rng.randint(0, 99)}"},
               "request": {"endpoint": eps[i % 5], "status": rng.choice([200, 200, 201, 404, 500]),
                           "latency_ms": round(rng.uniform(0.5, 900), 2)}}
        lines.append(json.dumps(rec))
    payload = "\n".join(lines) + "\n"
    (d / "input.txt").write_text(payload)
    (d / "input.ndjson").write_text(payload)


def gen_fd004(d):  # inventory_old.csv + inventory_new.csv
    rng = seed_for("FD-004")
    whs = [f"W{rng.randint(1, 12)}" for _ in range(8)]
    prods = [f"P{rng.randint(100, 999)}" for _ in range(30)]
    keys = [(rng.choice(whs), rng.choice(prods)) for _ in range(1500)]
    def snap(keys):
        rows = ["warehouse,product,quantity"]
        for w, p in keys:
            rows.append(f"{w},{p},{rng.randint(0, 500)}")
        return "\n".join(rows) + "\n"
    (d / "inventory_old.csv").write_text(snap(keys))
    (d / "inventory_new.csv").write_text(snap(keys[:1200] + keys[100:]))


def gen_fd005(d):  # CSV logs on stdin: timestamp,severity,message
    rng = seed_for("FD-005")
    sevs = ["INFO", "WARN", "ERROR", "DEBUG"]
    msgs = ["db query took 12ms", "cache miss", "user login ok",
            "job queued", "retrying request", "connection timeout"]
    lines = ["timestamp,severity,message"]
    for _ in range(N_BIG):
        ts = (f"2026-09-14T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:"
              f"{rng.randint(0, 59):02d}")
        lines.append(f"{ts},{sevs[rng.randint(0, 3)]},{rng.choice(msgs)}")
    (d / "input.txt").write_text("\n".join(lines) + "\n")


def gen_fd008(d):  # duplicate-finder: needs a directory tree
    rng = seed_for("FD-008")
    tree = d / "tree"
    tree.mkdir(parents=True, exist_ok=True)
    # subdirs with files, some exact duplicates (same content)
    for sub in ("docs", "photos", "logs"):
        (tree / sub).mkdir(exist_ok=True)
    blob = lambda i: f"content-{i}-" + "x" * 200
    for sub in ("docs", "photos", "logs"):
        for i in range(40):
            (tree / sub / f"f{i:03d}.txt").write_text(blob(i % 30))
    for i in range(10):
        (tree / f"root{i}.txt").write_text(blob(i))
    (d / "input.txt").write_text("tree\n")


# ---------- realistic_applications_utilities ----------

def gen_ra001(d):
    # deepseek variant: 8-option menu (add xN, view, stats, filter, search, exit)
    rng = seed_for("RA-001")
    cats = ["food", "travel", "shopping", "utilities", "health"]
    lines = []
    for i in range(50):
        lines += ["1", f"2026-01-{rng.randint(1, 28):02d}",
                  cats[i % 5], f"expense item {i}", str(rng.randint(10, 2000))]
    lines += ["2", ""]                     # view all (blank limit)
    lines += ["3"]                         # statistics
    lines += ["4", "food", "2026-01-01", "2026-12-31", "100", "1000"]
    lines += ["5", "item"]                 # search
    lines += ["8"]                         # exit
    (d / "input.txt").write_text("\n".join(lines) + "\n")
    # gemini variant: register -> quick add -> set budget -> logout -> exit
    g = ["2", "alice", "1", "lunch combo", "250.5", "1", "bus fare", "80",
         "2", "food", "5000", "4", "3"]
    (d / "input_gemini.txt").write_text("\n".join(g) + "\n")


def gen_fd003(d):  # sales.csv: region,category,units,unit_price
    rng = seed_for("FD-003")
    regions = ["north", "south", "east", "west", "central"]
    cats = ["electronics", "grocery", "apparel", "toys", "home"]
    rows = ["region,category,units,unit_price"]
    for _ in range(N_BIG):
        rows.append(f"{rng.choice(regions)},{rng.choice(cats)},"
                    f"{rng.randint(1, 500)},{rng.randint(1, 9999) / 100:.2f}")
    (d / "sales.csv").write_text("\n".join(rows) + "\n")


def gen_fd005(d):  # logs.csv: timestamp,severity,message
    rng = seed_for("FD-005")
    sevs = ["INFO", "WARN", "ERROR", "DEBUG"]
    rows = ["timestamp,severity,message"]
    for _ in range(N_BIG):
        ts = (f"2026-09-14T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:"
              f"{rng.randint(0, 59):02d}")
        rows.append(f"{ts},{sevs[rng.randint(0, 3)]},event {rng.randint(0, 9999)}")
    (d / "logs.csv").write_text("\n".join(rows) + "\n")


def gen_fd006(d):  # data.csv: generic columns
    rng = seed_for("FD-006")
    rows = ["id,name,score,date"]
    for i in range(N_BIG):
        rows.append(f"{i},user{rng.randint(0, 999)},{rng.randint(0, 100)},"
                    f"2026-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}")
    (d / "data.csv").write_text("\n".join(rows) + "\n")


def gen_fd007(d):  # events.csv: user,timestamp,event
    rng = seed_for("FD-007")
    events = ["login", "logout", "view", "click", "purchase"]
    rows = ["user,timestamp,event"]
    t = 0
    for _ in range(N_BIG):
        t += rng.randint(1, 100)
        rows.append(f"u{rng.randint(0, 300)},{t},{rng.choice(events)}")
    (d / "events.csv").write_text("\n".join(rows) + "\n")


def gen_fd009(d):  # transactions.csv: transaction_id,account_id,timestamp,amount
    rng = seed_for("FD-009")
    rows = ["transaction_id,account_id,timestamp,amount"]
    for i in range(N_BIG):
        rows.append(f"T{i:07d},A{rng.randint(0, 400):05d},{rng.randint(0, 10**6)},"
                    f"{rng.randint(1, 100000) / 100:.2f}")
    (d / "transactions.csv").write_text("\n".join(rows) + "\n")


def gen_fd010(d):  # input.json: products -> warehouses
    rng = seed_for("FD-010")
    prods = []
    for i in range(1500):
        prods.append({
            "product_id": f"P{i:05d}", "name": f"product {i}",
            "warehouses": [{"warehouse_id": f"W{rng.randint(1, 20)}",
                            "stock": rng.randint(0, 500)} for _ in range(rng.randint(1, 3))],
        })
    (d / "input.json").write_text(json.dumps({"products": prods}))


TASKS = {
    "file_data_processing/FD-003": gen_fd003,
    "file_data_processing/FD-005": gen_fd005,
    "file_data_processing/FD-006": gen_fd006,
    "file_data_processing/FD-007": gen_fd007,
    "file_data_processing/FD-009": gen_fd009,
    "file_data_processing/FD-010": gen_fd010,
    "algorithms_computation/AC-001": gen_ac001,
    "algorithms_computation/AC-003": gen_ac003,
    "algorithms_computation/AC-004": gen_ac004,
    "algorithms_computation/AC-005": gen_ac005,
    "algorithms_computation/AC-006": gen_ac006,
    "algorithms_computation/AC-007": gen_ac007,
    "algorithms_computation/AC-008": gen_ac008,
    "algorithms_computation/AC-010": gen_ac010,
    "algorithms_computation/AC-013": gen_ac013,
    "algorithms_computation/AC-015": gen_ac015,
    "file_data_processing/FD-001": gen_fd001,
    "file_data_processing/FD-002": gen_fd002,
    "file_data_processing/FD-004": gen_fd004,
    "file_data_processing/FD-005": gen_fd005,
    "file_data_processing/FD-008": gen_fd008,
    "realistic_applications_utilities/RA-001": gen_ra001,
}


def main():
    for rel, gen in sorted(TASKS.items()):
        d = INPUTS / rel
        d.mkdir(parents=True, exist_ok=True)
        gen(d)
        print(f"generated {rel}: {sorted(p.name for p in d.iterdir())}")


if __name__ == "__main__":
    main()
