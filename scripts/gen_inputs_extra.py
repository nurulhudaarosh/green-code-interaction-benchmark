#!/usr/bin/env python3
"""Extended per-task input generators.

Companion to scripts/gen_inputs.py: generates deterministic workloads for the
tasks that arrived in later member ZIPs (FD-011..018, TL-002/004/005,
RA-002/004/006) and image directories for image_media_processing. Output goes
to inputs/<category>/<task_id>/ exactly like gen_inputs.py so the measurement
runner (scripts/measure_energy.py) serves it unchanged.

Deterministic (seeded from task_id / names), offline, standard library only
(PIL only for image tasks).
"""
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path("/home/arosh/code/green-code-interaction-benchmark")
INPUTS = REPO / "inputs"
N = 20000


def seed_for(tid):
    return random.Random(sum(ord(c) for c in tid) & 0xFFFF)


def write_csv(d, name, header, rows):
    (d / name).write_text(",".join(header) + "\n" + "\n".join(rows) + "\n")


# ---------------------------------------------------------------- FD

def gen_fd011(d):  # time-series gap filling: sensor,timestamp,value
    rng = seed_for("FD-011")
    rows, t0 = [], datetime(2026, 1, 1)
    for s in range(6):
        t = t0 + timedelta(minutes=s)
        for _ in range(3000):
            t += timedelta(minutes=rng.choice([1, 1, 1, 2, 5, 15, 60]))
            rows.append(f"S{s},S{s},{t.isoformat()},{rng.uniform(0, 100):.3f}")
    body = "sensor_id,sensor,timestamp,value\n" + "\n".join(rows) + "\n"
    for name in ("readings.csv", "sensor_readings.csv", "input.csv", "sensor_data.csv"):
        (d / name).write_text(body)


def gen_fd012(d):  # word frequency over a directory of .txt files
    rng = seed_for("FD-012")
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
             "theta", "iota", "kappa", "the", "and", "of", "to", "data"]
    for sub in ("texts", "docs", "input", "input_dir"):
        sd = d / sub
        sd.mkdir(parents=True, exist_ok=True)
        for i in range(200):
            lines = [" ".join(rng.choice(words) for _ in range(rng.randint(20, 80)))
                     for _ in range(rng.randint(5, 20))]
            (sd / f"doc{i:03d}.txt").write_text("\n".join(lines) + "\n")
    (d / "input.txt").write_text(" ".join(rng.choice(words) for _ in range(5000)) + "\n")


def gen_fd013(d):  # per-column CSV statistics
    rng = seed_for("FD-013")
    rows = []
    for i in range(N):
        cells = []
        for _ in range(3):
            cells.append("" if rng.random() < 0.02 else f"{rng.uniform(-100, 100):.4f}")
        rows.append(f"row{i}," + ",".join(cells))
    body = "id,value1,value2,value3\n" + "\n".join(rows) + "\n"
    for name in ("data.csv", "sample_data.csv", "input.csv"):
        (d / name).write_text(body)
    (d / "edge_case_data.csv").write_text(
        "id,value1,value2,value3\na,1,2,3\nb,,5,6\nc,7,8,\n")


def gen_fd014(d):  # record linkage with blocking (two CSVs)
    rng = seed_for("FD-014")
    names = [f"Person{i}" for i in range(500)]
    left = ["id,name,surname,email,phone,postal_code"]
    right = ["id,name,surname,email,phone,postal_code"]
    for i in range(4000):
        c = rng.randint(0, 499)
        pc = rng.randint(10000, 99999)
        left.append(f"L{i},{names[c]},Sur{rng.randint(0, 99)},"
                    f"user{c}@mail.com,+1555{rng.randint(0, 9999):04d},{pc}")
        if rng.random() < 0.6:
            right.append(f"R{i},{names[c]},Sur{rng.randint(0, 99)},"
                         f"user{c}@mail.com,+1555{rng.randint(0, 9999):04d},{pc}")
        else:
            right.append(f"R{i},Other{i},X,other{i}@x.com,"
                         f"+1666{i % 10000:04d},{rng.randint(10000, 99999)}")
    (d / "left.csv").write_text("\n".join(left) + "\n")
    (d / "right.csv").write_text("\n".join(right) + "\n")
    (d / "inputs").mkdir(exist_ok=True)


def gen_fd015(d):  # JSONL sort-filter pipeline
    rng = seed_for("FD-015")
    cats = ["a", "b", "c", "d"]
    lines = []
    for i in range(N):
        lines.append(json.dumps({"id": f"id{i}", "category": rng.choice(cats),
                                 "score": round(rng.uniform(0, 100), 3),
                                 "active": rng.random() < 0.5}))
    body = "\n".join(lines) + "\n"
    for name in ("input.jsonl", "records.jsonl"):
        (d / name).write_text(body)


def gen_fd016(d):  # multi-file merge join (customers + transactions)
    rng = seed_for("FD-016")
    cust = ["customer_id,name,region"]
    for i in range(3000):
        cust.append(f"C{i:05d},Customer {i},R{i % 8}")
    tx = ["transaction_id,customer_id,amount"]
    for i in range(N):
        tx.append(f"T{i:06d},C{rng.randint(0, 2999):05d},{rng.uniform(1, 500):.2f}")
    (d / "customers.csv").write_text("\n".join(cust) + "\n")
    (d / "transactions.csv").write_text("\n".join(tx) + "\n")


def gen_fd017(d):  # event type pivot table
    rng = seed_for("FD-017")
    regions = ["north", "south", "east", "west"]
    events = ["view", "click", "purchase", "signup"]
    rows = ["date,region,event_type,count"]
    for i in range(N):
        rows.append(f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d},"
                    f"{regions[rng.randint(0, 3)]},{events[rng.randint(0, 3)]},"
                    f"{rng.randint(1, 100)}")
    (d / "events.csv").write_text("\n".join(rows) + "\n")


def gen_fd018(d):  # duplicate normalized records
    rng = seed_for("FD-018")
    words = ["alpha", "beta", "gamma", "delta", "epsilon"]
    rows = ["record_id,id,title,description,date,text"]
    for i in range(N):
        w = rng.choice(words)
        rows.append(f"R{i:06d},R{i:06d},Title {w},{w} description "
                    f"{rng.randint(0, 50)},2026-01-{(i % 28) + 1:02d},{w} body")
    (d / "records.csv").write_text("\n".join(rows) + "\n")


# ---------------------------------------------------------------- TL

def gen_tl002(d):  # access log -> CSV
    rng = seed_for("TL-002")
    methods = ["GET", "POST", "PUT", "DELETE"]
    paths = ["/", "/index.html", "/api/data", "/api/items/1", "/login",
             "/logout", "/img/logo.png", "/static/app.js"]
    statuses = [200, 200, 200, 201, 204, 301, 404, 500]
    lines = []
    base = datetime(2026, 3, 1, 0, 0, 0)
    for i in range(30000):
        base += timedelta(seconds=rng.randint(1, 5))
        ts = base.strftime("%d/%b/%Y:%H:%M:%S +0000")
        lines.append(f'10.0.{rng.randint(0, 255)}.{rng.randint(1, 254)} - user{rng.randint(0, 50)} '
                     f'[{ts}] "{methods[rng.randint(0, 3)]} {paths[rng.randint(0, 7)]} HTTP/1.1" '
                     f'{statuses[rng.randint(0, 7)]} {rng.randint(100, 9000)} "-" "Mozilla/5.0"')
    body = "\n".join(lines) + "\n"
    (d / "access.log").write_text(body)
    (d / "input_log.txt").write_text(body)
    (d / "input.txt").write_text(body)


def gen_tl004(d):  # concordance / word frequency document
    rng = seed_for("TL-004")
    vocab = ("the quick brown fox jumps over a lazy dog and then runs far away "
             "data science machine learning energy efficiency benchmark code "
             "python software engineering measurement interaction style test").split()
    lines = [" ".join(rng.choice(vocab) for _ in range(rng.randint(8, 25)))
             for _ in range(5000)]
    body = "\n".join(lines) + "\n"
    (d / "document.txt").write_text(body)
    (d / "input.txt").write_text(body)
    (d / "a.txt").write_text(body)


def gen_tl005(d):  # duplicate-line detection over a directory + list
    rng = seed_for("TL-005")
    base = [f"2026-03-01T{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:00 "
            f"level={rng.choice(['INFO', 'WARN', 'ERROR'])} "
            f"msg=event-{rng.randint(0, 200)}" for _ in range(400)]
    lines = [base[rng.randint(0, len(base) - 1)] for _ in range(20000)]
    body = "\n".join(lines) + "\n"
    (d / "input.txt").write_text(body)
    (d / "logs.txt").write_text(body)
    for sub in ("input", "input_dir"):
        sd = d / sub
        sd.mkdir(parents=True, exist_ok=True)
        for i in range(150):
            chunk = [lines[rng.randint(0, len(lines) - 1)] for _ in range(80)]
            (sd / f"log{i:03d}.txt").write_text("\n".join(chunk) + "\n")


# ---------------------------------------------------------------- RA

def gen_ra002(d):
    rng = seed_for("RA-002")
    products = [{"sku": f"SKU{i:05d}", "name": f"Product {i}",
                 "stock": rng.randint(0, 200), "reorder_level": rng.randint(5, 50)}
                for i in range(2000)]
    sales = [{"sku": f"SKU{rng.randint(0, 2500):05d}", "quantity": rng.randint(1, 20)}
             for _ in range(8000)]
    payload = {"products": products, "sales": sales}
    (d / "input.json").write_text(json.dumps(payload))
    (d / "data.json").write_text(json.dumps(payload))


def gen_ra004(d):  # offline document organizer over a directory tree
    rng = seed_for("RA-004")
    (d / "input").mkdir(exist_ok=True)
    (d / "sample_dir").mkdir(exist_ok=True)
    exts = [".txt", ".pdf", ".jpg", ".png", ".csv", ".json", ".md", ".log"]
    for i in range(60):
        for base in ("input", "sample_dir"):
            ext = exts[rng.randint(0, len(exts) - 1)]
            (d / base / f"file{i:03d}{ext}").write_text(
                "x" * rng.randint(10, 400))
    for name in ("a.txt", "old.txt", "document.txt", "empty.txt"):
        (d / name).write_text("" if name == "empty.txt" else "content\n" * 5)


def gen_ra006(d):  # configuration validator
    rng = seed_for("RA-006")
    cfg = {"name": "service", "port": 8080, "debug": False,
           "workers": 4, "timeout": 30, "retries": 3,
           "log_level": "info", "tags": ["a", "b"]}
    for i in range(50):
        cfg[f"opt_{i}"] = rng.randint(0, 100)
    (d / "config.json").write_text(json.dumps(cfg, indent=2))
    (d / "schema.json").write_text(json.dumps(
        {"name": "str", "port": "int", "debug": "bool"}, indent=2))


# ---------------------------------------------------------------- IM

def _noise_image(path, size, ext):
    from PIL import Image
    w, h = size
    img = Image.frombytes("RGB", (w, h), os.urandom(w * h * 3))
    path.parent.mkdir(parents=True, exist_ok=True)
    if ext in (".jpg", ".jpeg"):
        img.save(path, quality=90)
    else:
        img.save(path)


def gen_im_common(d):
    sizes = [(64, 48), (128, 96), (32, 32), (200, 150), (64, 64), (96, 128)]
    dirs = ["input_dir", "input_images", "input_folder", "images", "photos",
            "sample_images", "photo_folder", "input"]
    for i, sub in enumerate(dirs):
        sd = d / sub
        sd.mkdir(parents=True, exist_ok=True)
        for j, size in enumerate(sizes):
            head = (j + i) % 2
            ext = ".jpg" if head else ".png"
            _noise_image(sd / f"img{j}{ext}", size, ext)
    # individual names some programs hard-code
    singles = ["image.jpg", "image1.jpg", "img1.jpg", "cat.jpg", "photo.jpg",
               "a.png", "b.png", "c.png", "in.png", "good.png", "broken.png",
               "only.png", "one.png", "foo.png", "restored.png", "flat.png",
               "grad.png", "black.png", "white.png"]
    for i, name in enumerate(singles):
        _noise_image(d / name, sizes[i % len(sizes)], Path(name).suffix)
    _noise_image(d / "pets" / "cat.jpg", (80, 60), ".jpg")
    _noise_image(d / "small" / "cat.jpg", (40, 30), ".jpg")
    _noise_image(d / "channels" / "photo_R.png", (64, 64), ".png")
    _noise_image(d / "channels" / "photo_G.png", (64, 64), ".png")
    _noise_image(d / "channels" / "photo_B.png", (64, 64), ".png")
    (d / "readme.txt").write_text("sample images\n")


TASKS = {
    "file_data_processing/FD-011": gen_fd011,
    "file_data_processing/FD-012": gen_fd012,
    "file_data_processing/FD-013": gen_fd013,
    "file_data_processing/FD-014": gen_fd014,
    "file_data_processing/FD-015": gen_fd015,
    "file_data_processing/FD-016": gen_fd016,
    "file_data_processing/FD-017": gen_fd017,
    "file_data_processing/FD-018": gen_fd018,
    "text_log_processing/TL-002": gen_tl002,
    "text_log_processing/TL-004": gen_tl004,
    "text_log_processing/TL-005": gen_tl005,
    "realistic_applications_utilities/RA-002": gen_ra002,
    "realistic_applications_utilities/RA-004": gen_ra004,
    "realistic_applications_utilities/RA-006": gen_ra006,
}
for _i in range(1, 26):
    TASKS[f"image_media_processing/IM-{_i:03d}"] = gen_im_common


def main():
    for rel, gen in sorted(TASKS.items()):
        d = INPUTS / rel
        d.mkdir(parents=True, exist_ok=True)
        gen(d)
        n = sum(1 for p in d.rglob("*") if p.is_file())
        print(f"generated {rel}: {n} files")


if __name__ == "__main__":
    main()
