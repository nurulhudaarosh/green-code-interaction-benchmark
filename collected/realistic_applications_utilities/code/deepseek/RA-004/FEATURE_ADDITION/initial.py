"""
Complete Document Organizer (v4)
--------------------------------
A fully functional document organizer that:
- Scans a source folder for files
- Categorizes them by type (Documents, Images, Videos, Audio, Archives, Code, etc.)
- Categorizes them by size bucket (Tiny/Small/Medium/Large/Huge) [NEW in v4]
- Moves (or copies) them into organized subfolders
- Handles duplicate filenames safely
- Supports dry-run mode
- Logs all actions
- Can undo the last organization (via manifest file)

BUILD HISTORY
=============
v1: Initial build — scan, categorize, move/copy, dry-run, undo via manifest.

v2 FIXES (extension + malformed-date handling):
  Extension:
    - Multi-part extensions (".tar.gz") match as a single unit.
    - Trailing-dot files ("report.") -> no extension -> "Others".
    - Hidden dotfiles (".bashrc") -> no extension -> "Others".
    - Surrounding whitespace trimmed before matching.
    - Explicit `get_extension()` helper, case-insensitive.
  Malformed dates:
    - Manifest entries carry an ISO timestamp.
    - `parse_timestamp()` safely returns None on malformed input.
    - `load_manifest()` validates structure and filters bad entries.
    - Backwards compatible with legacy string-only manifests.

v3 FIXES (deeper edge cases for extension + date handling):
  Extension:
    - Names that are just dots ("." / ".." / "...") -> no extension.
    - All-dot suffixes ("report..") -> no extension.
    - Path separators stripped (defense-in-depth).
    - Unicode NFKC normalization for full-width chars.
    - Precomputed ext->category map for O(1) lookup.
  Malformed dates:
    - Rejects control chars, multiple TZ designators, out-of-range years.
    - Accepts datetime objects and common alternate formats.
    - Malformed entries are quarantined to `.organizer_manifest.bad.json`.
    - Manifest gains a version field.

v4 (this version) — SIZE-BUCKET CLASSIFICATION:
  New feature:
    - Files are now ALSO classified by size into one of:
        Tiny   : < 64 KiB
        Small  : 64 KiB – 1 MiB
        Medium : 1 MiB – 16 MiB
        Large  : 16 MiB – 256 MiB
        Huge   : >= 256 MiB
    - Two new layout strategies via --layout:
        * "type"      (default, v1–v3 behavior)
              source/Documents/file.pdf
        * "size"      -> source/Medium/file.pdf
        * "type-size" -> source/Documents/Medium/file.pdf
        * "size-type" -> source/Medium/Documents/file.pdf
    - The manifest records the size of each file and the bucket used,
      so `--undo` can restore reliably regardless of layout.
    - Backwards compatible: old manifests (v1/v2) still undo fine.
    - `--dry-run` prints the chosen layout path.
    - Configurable thresholds via `--size-thresholds` (KiB,MiB,...) if
      you want to override the defaults.
    - Self-test extended to cover boundary cases (0 bytes, exact
      thresholds, huge files simulated via metadata).

Usage:
    python document_organizer.py /path/to/folder [--copy] [--dry-run] [--undo]
                                 [--layout {type,size,type-size,size-type}]
                                 [--size-thresholds K,M,G,...]
    python document_organizer.py --self-test

Examples:
    python document_organizer.py ~/Downloads
    python document_organizer.py ~/Downloads --layout size
    python document_organizer.py ~/Downloads --layout type-size
    python document_organizer.py ~/Downloads --copy --layout size-type
    python document_organizer.py ~/Downloads --dry-run
    python document_organizer.py ~/Downloads --undo
"""

import os
import sys
import shutil
import argparse
import json
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict


# ---------- Category definitions ----------
CATEGORIES = {
    "Documents": [
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
        ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"
    ],
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
        ".webp", ".tiff", ".ico", ".heic"
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpg", ".mpeg"
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
        ".m4a", ".opus"
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso",
        ".tar.gz", ".tar.bz2", ".tar.xz", ".tar.zst"
    ],
    "Code": [
        ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".rb",
        ".go", ".rs", ".php", ".html", ".css", ".scss", ".json",
        ".xml", ".yml", ".yaml", ".sh", ".bat", ".sql"
    ],
    "Executables": [
        ".exe", ".msi", ".app", ".deb", ".rpm", ".apk", ".dmg"
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot"
    ],
    "Ebooks": [
        ".epub", ".mobi", ".azw", ".azw3", ".fb2"
    ],
}

# Longest multi-part extensions first so ".tar.gz" wins over ".gz".
MULTIPART_EXTENSIONS = sorted(
    (ext for ext in CATEGORIES["Archives"] if ext.count(".") > 1),
    key=len,
    reverse=True,
)

# Precomputed ext -> category map for O(1) lookup.
_EXT_TO_CATEGORY = {}
for _cat, _exts in CATEGORIES.items():
    for _ext in _exts:
        _EXT_TO_CATEGORY[_ext.lower()] = _cat


# ---------- Size-bucket definitions (v4) ----------
# Buckets are (name, min_inclusive_bytes, max_exclusive_bytes|None).
# Default thresholds (in bytes):
#   Tiny   : [0,              64 KiB)
#   Small  : [64 KiB,          1 MiB)
#   Medium : [1 MiB,          16 MiB)
#   Large  : [16 MiB,        256 MiB)
#   Huge   : [256 MiB,         None)
KIB = 1024
MIB = 1024 * 1024
GIB = 1024 * 1024 * 1024

DEFAULT_SIZE_BUCKETS = [
    ("Tiny",   0,             64 * KIB),
    ("Small",  64 * KIB,       1 * MIB),
    ("Medium", 1 * MIB,       16 * MIB),
    ("Large",  16 * MIB,     256 * MIB),
    ("Huge",   256 * MIB,     None),
]

# Sanity range for dates.
_MIN_YEAR = 1970
_MAX_YEAR = 9999

_ALT_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
)

MANIFEST_NAME = ".organizer_manifest.json"
MANIFEST_BAD_NAME = ".organizer_manifest.bad.json"
MANIFEST_VERSION = 3  # bumped in v4 for size metadata

LAYOUTS = ("type", "size", "type-size", "size-type")


# ---------- Helpers: extension handling (v3) ----------
def _normalize_for_ext(name: str) -> str:
    try:
        return unicodedata.normalize("NFKC", name).casefold()
    except (TypeError, ValueError):
        return name.casefold() if isinstance(name, str) else ""


def get_extension(filename: str) -> str:
    """Extract a normalized (lowercase) extension, or "" if none."""
    if not isinstance(filename, str):
        return ""
    name = filename.strip()
    if not name:
        return ""
    if "/" in name or "\\" in name or os.sep in name:
        name = os.path.basename(name.replace("\\", "/"))
        if not name:
            return ""
    if set(name) == {"."}:
        return ""
    if name.startswith(".") and name.count(".") == 1:
        return ""
    if "." not in name:
        return ""
    if name.endswith("."):
        return ""
    folded = _normalize_for_ext(name)
    for ext in MULTIPART_EXTENSIONS:
        if folded.endswith(ext):
            return ext
    _, _, tail = folded.rpartition(".")
    if not tail or set(tail) == {"."}:
        return ""
    return "." + tail


def get_category(filename_or_ext: str) -> str:
    """Return category name for a filename or bare extension."""
    if not isinstance(filename_or_ext, str):
        return "Others"
    s = filename_or_ext.strip()
    if not s:
        return "Others"
    if s.startswith(".") and "/" not in s and "\\" not in s and s.count(".") >= 1:
        ext = _normalize_for_ext(s)
    else:
        ext = get_extension(s)
    if not ext:
        return "Others"
    return _EXT_TO_CATEGORY.get(ext, "Others")


# ---------- Helpers: size buckets (v4) ----------
def get_size_bucket(size_bytes: int, buckets=None) -> str:
    """
    Return the size-bucket name for a file size in bytes.
    Uses half-open ranges [min, max). The final bucket may have max=None
    (open-ended).
    """
    if not isinstance(size_bytes, int) or size_bytes < 0:
        return "Unknown"
    buckets = buckets or DEFAULT_SIZE_BUCKETS
    for name, lo, hi in buckets:
        if size_bytes >= lo and (hi is None or size_bytes < hi):
            return name
    return "Unknown"


def parse_size_thresholds(spec: str):
    """
    Parse a comma-separated list of thresholds into buckets.
    Example: "64K,1M,16M,256M" produces:
        Tiny/Small/Medium/Large/Huge
    Units: K=KiB, M=MiB, G=GiB (case-insensitive). Bare numbers = bytes.
    Returns None if the spec is empty/None. Raises ValueError on bad input.
    """
    if not spec:
        return None
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if not parts:
        return None

    def parse_one(p):
        p = p.strip()
        unit = p[-1].upper() if p else ""
        mult = {"K": KIB, "M": MIB, "G": GIB}.get(unit)
        if mult is not None:
            num = p[:-1]
        else:
            mult = 1
            num = p
        if not num:
            raise ValueError(f"Bad threshold: {p!r}")
        try:
            val = int(float(num) * mult)
        except (ValueError, TypeError):
            raise ValueError(f"Bad threshold: {p!r}")
        if val < 0:
            raise ValueError(f"Negative threshold: {p!r}")
        return val

    values = [parse_one(p) for p in parts]
    # Strictly increasing.
    for a, b in zip(values, values[1:]):
        if b <= a:
            raise ValueError("Thresholds must be strictly increasing")

    names = ["Tiny", "Small", "Medium", "Large", "Huge"]
    # If user provided N thresholds, we have N+1 buckets.
    if len(values) + 1 != len(names):
        # Fall back to generic names if count doesn't match defaults.
        names = [f"Bucket{i}" for i in range(len(values) + 1)]

    buckets = []
    prev = 0
    for name, hi in zip(names, values):
        buckets.append((name, prev, hi))
        prev = hi
    buckets.append((names[-1], prev, None))
    return buckets


# ---------- Helpers: malformed-date handling (v3) ----------
def parse_timestamp(value) -> datetime | None:
    """Safely parse a timestamp into a datetime. Returns None if malformed."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return _clamp_year(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if any(ord(ch) < 0x20 for ch in s):
        return None
    if s.count("Z") + s.count("z") > 1:
        return None
    if s.count("+") > 1:
        return None

    candidate = s.replace("Z", "+00:00").replace("z", "+00:00")
    dt = None
    try:
        dt = datetime.fromisoformat(candidate)
    except (ValueError, TypeError):
        dt = None

    if dt is None:
        for fmt in _ALT_DATE_FORMATS:
            try:
                dt = datetime.strptime(s, fmt)
                break
            except (ValueError, TypeError):
                continue

    if dt is None:
        return None
    return _clamp_year(dt)


def _clamp_year(dt: datetime) -> datetime | None:
    if _MIN_YEAR <= dt.year <= _MAX_YEAR:
        return dt
    return None


def is_valid_manifest_entry(entry) -> bool:
    """Validate a manifest entry (v1 string or v2/v3 dict)."""
    if isinstance(entry, str):
        return bool(entry.strip())
    if isinstance(entry, dict):
        dest = entry.get("dest")
        return isinstance(dest, str) and bool(dest.strip())
    return False


# ---------- Helpers: file/dir utilities ----------
def unique_destination(dest_path: Path) -> Path:
    """If a file already exists at dest_path, append (1), (2), ... until unique."""
    if not dest_path.exists():
        return dest_path
    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _quarantine_bad_entries(folder: Path, bad: dict) -> None:
    if not bad:
        return
    try:
        path = folder / MANIFEST_BAD_NAME
        existing = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, dict):
                    existing = {}
            except (json.JSONDecodeError, OSError):
                existing = {}
        existing.update(bad)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        log(f"Quarantined {len(bad)} malformed entry(ies) -> {MANIFEST_BAD_NAME}")
    except OSError as e:
        log(f"Warning: could not write quarantine file: {e}")


def load_manifest(folder: Path) -> dict:
    """Load the manifest, filtering/quarantining malformed entries."""
    manifest_path = folder / MANIFEST_NAME
    if not manifest_path.exists():
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f"Warning: could not read manifest ({e}). Starting fresh.")
        return {}

    if isinstance(raw, dict) and "entries" in raw and isinstance(raw["entries"], dict):
        entries = raw["entries"]
    elif isinstance(raw, dict):
        entries = raw
    else:
        log("Warning: manifest has unexpected structure. Ignoring.")
        return {}

    cleaned = {}
    bad = {}
    for original, entry in entries.items():
        if not isinstance(original, str) or not original.strip():
            bad[repr(original)] = entry
            continue
        if not is_valid_manifest_entry(entry):
            bad[original] = entry
            continue

        if isinstance(entry, str):
            cleaned[original] = {"dest": entry, "timestamp": None, "size": None}
        else:
            ts_raw = entry.get("timestamp")
            ts = parse_timestamp(ts_raw)
            if ts_raw is not None and ts is None:
                log(f"Warning: malformed timestamp for {original!r}: {ts_raw!r}")
                bad.setdefault(original, {
                    "dest": entry["dest"],
                    "timestamp": ts_raw,
                    "reason": "malformed_timestamp",
                })
            # Preserve size when valid.
            size = entry.get("size")
            if not isinstance(size, int) or size < 0:
                size = None
            cleaned[original] = {
                "dest": entry["dest"],
                "timestamp": ts.isoformat() if ts else None,
                "size": size,
            }

    _quarantine_bad_entries(folder, bad)
    return cleaned


def save_manifest(folder: Path, manifest: dict) -> None:
    """Save the manifest in v3 format (adds size + bucket metadata)."""
    manifest_path = folder / MANIFEST_NAME
    payload = {
        "version": MANIFEST_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entries": manifest,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


# ---------- Layout planning (v4) ----------
def _safe_stat_size(path: Path) -> int:
    """Return file size in bytes, or 0 if it can't be stat'd."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


def plan_relative_dir(file_path: Path, layout: str, size_buckets) -> Path:
    """
    Return the RELATIVE directory (from source root) where file_path should go,
    given a layout and size buckets.
    """
    if layout not in LAYOUTS:
        raise ValueError(f"Unknown layout: {layout}")

    type_dir = get_category(file_path.name)
    size = _safe_stat_size(file_path)
    size_dir = get_size_bucket(size, size_buckets)

    if layout == "type":
        return Path(type_dir)
    if layout == "size":
        return Path(size_dir)
    if layout == "type-size":
        return Path(type_dir) / size_dir
    if layout == "size-type":
        return Path(size_dir) / type_dir
    # unreachable
    return Path("Others")


# ---------- Core operations ----------
def scan_files(source: Path):
    """Yield files directly inside source, excluding manifest files."""
    for entry in source.iterdir():
        if not entry.is_file():
            continue
        if entry.name in (MANIFEST_NAME, MANIFEST_BAD_NAME):
            continue
        yield entry


def organize(source: Path, copy: bool = False, dry_run: bool = False,
             layout: str = "type", size_buckets=None) -> dict:
    """
    Organize files in `source` into category/size subfolders.
    Returns a manifest dict: {original: {"dest": ..., "timestamp": ...,
                                        "size": ..., "layout": ...}}.
    """
    if not source.exists() or not source.is_dir():
        raise NotADirectoryError(f"Not a valid directory: {source}")
    if layout not in LAYOUTS:
        raise ValueError(f"Unknown layout: {layout}")

    moved = {}
    stats = defaultdict(int)

    files = list(scan_files(source))
    if not files:
        log("No files found to organize.")
        return moved

    log(f"Found {len(files)} file(s) in '{source}'")
    log(f"Mode: {'COPY' if copy else 'MOVE'}{' (DRY RUN)' if dry_run else ''}")
    log(f"Layout: {layout}")
    log("-" * 50)

    for file_path in files:
        rel_dir = plan_relative_dir(file_path, layout, size_buckets)
        target_dir = source / rel_dir
        dest_path = unique_destination(target_dir / file_path.name)
        size = _safe_stat_size(file_path)
        bucket = get_size_bucket(size, size_buckets)

        try:
            if dry_run:
                log(f"[DRY] {file_path.name}  ->  {rel_dir}/  "
                    f"[{bucket}, {human_size(size)}]")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                if copy:
                    shutil.copy2(file_path, dest_path)
                else:
                    shutil.move(str(file_path), str(dest_path))
                log(f"{file_path.name}  ->  {rel_dir}/{dest_path.name}  "
                    f"[{bucket}, {human_size(size)}]")
                moved[str(file_path)] = {
                    "dest": str(dest_path),
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "size": size,
                    "bucket": bucket,
                    "layout": layout,
                }
            stats[f"{rel_dir}"] += 1
        except (OSError, shutil.Error) as e:
            log(f"ERROR moving '{file_path.name}': {e}")

    log("-" * 50)
    log("Summary:")
    for key, count in sorted(stats.items()):
        log(f"  {key:<30} {count} file(s)")

    return moved


def undo(source: Path) -> None:
    """Undo the last organization using the manifest file."""
    manifest = load_manifest(source)
    if not manifest:
        log("No valid manifest entries found. Nothing to undo.")
        return

    log(f"Undoing {len(manifest)} operation(s)...")
    errors = 0
    skipped = 0

    for original, entry in manifest.items():
        current = entry.get("dest")
        ts = parse_timestamp(entry.get("timestamp"))

        if not isinstance(current, str) or not current.strip():
            log(f"SKIP (malformed dest): {original!r}")
            skipped += 1
            continue

        original_path = Path(original)
        current_path = Path(current)

        if entry.get("timestamp") and ts is None:
            log(f"Note: malformed timestamp for '{current_path.name}' "
                f"(proceeding anyway)")
        elif ts is not None:
            log(f"  (from {ts.strftime('%Y-%m-%d %H:%M:%S')})")

        if not current_path.exists():
            log(f"SKIP (missing): {current_path}")
            skipped += 1
            continue

        if original_path.exists():
            log(f"SKIP (target exists): {original_path}")
            errors += 1
            continue

        try:
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(original_path))
            log(f"Restored: {current_path.name}  ->  {original_path.parent.name}/")
        except (OSError, shutil.Error) as e:
            log(f"ERROR restoring '{current_path.name}': {e}")
            errors += 1

    # Prune empty dirs we may have created (recursively but safely).
    _prune_empty_dirs(source)

    manifest_path = source / MANIFEST_NAME
    if manifest_path.exists():
        manifest_path.unlink()

    if errors == 0 and skipped == 0:
        log("Undo complete.")
    else:
        log(f"Undo complete with {errors} error(s) and {skipped} skipped.")


def _prune_empty_dirs(root: Path) -> None:
    """Remove empty subdirectories under root (not root itself)."""
    # Walk bottom-up.
    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        p = Path(dirpath)
        if p == root:
            continue
        try:
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
                log(f"Removed empty folder: {p.relative_to(root)}/")
        except OSError:
            pass


def human_size(n: int) -> str:
    """Format a byte count as a human-readable string."""
    if not isinstance(n, int) or n < 0:
        return "?"
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(size)} {u}"
            return f"{size:.1f} {u}"
        size /= 1024


# ---------- Self-test ----------
def _self_test() -> None:
    """Sanity checks for v4 extension + timestamp + size-bucket handling."""
    ext_cases = [
        ("report.pdf", ".pdf", "Documents"),
        ("REPORT.PDF", ".pdf", "Documents"),
        ("archive.tar.gz", ".tar.gz", "Archives"),
        ("backup.tar.bz2", ".tar.bz2", "Archives"),
        ("data.tar", ".tar", "Archives"),
        ("no_extension", "", "Others"),
        ("trailingdot.", "", "Others"),
        ("trailingdots..", "", "Others"),
        ("all...", "", "Others"),
        (".bashrc", "", "Others"),
        (".gitignore", "", "Others"),
        (".", "", "Others"),
        ("..", "", "Others"),
        ("...", "", "Others"),
        ("   ", "", "Others"),
        ("", "", "Others"),
        ("file.pdf ", ".pdf", "Documents"),
        ("  file.pdf", ".pdf", "Documents"),
        ("my.file.name.PNG", ".png", "Images"),
        ("FILE.ＰＤＦ", ".pdf", "Documents"),
        ("weird/pa.th.pdf", ".pdf", "Documents"),
        ("weird\\pa.th.pdf", ".pdf", "Documents"),
        ("script.PY", ".py", "Code"),
        ("archive.TAR.GZ", ".tar.gz", "Archives"),
    ]
    for name, exp_ext, exp_cat in ext_cases:
        got_ext = get_extension(name)
        got_cat = get_category(name)
        assert got_ext == exp_ext, f"ext({name!r}) = {got_ext!r} != {exp_ext!r}"
        assert got_cat == exp_cat, f"cat({name!r}) = {got_cat!r} != {exp_cat!r}"

    # Timestamps — valid.
    for v in [
        "2024-01-15T10:30:00", "2024-01-15T10:30:00Z",
        "2024-01-15T10:30:00+05:00", "2024-01-15 10:30:00",
        "2024/01/15 10:30:00", "2024/01/15", "15-01-2024", "15/01/2024",
        datetime(2024, 1, 15, 10, 30),
    ]:
        assert parse_timestamp(v) is not None, f"expected valid: {v!r}"

    # Timestamps — invalid.
    for v in [
        None, "", "   ", 12345, 3.14, [], {}, object(),
        "not-a-date", "2024-13-45", "01/99/2024",
        "2024-01-15T10:30:00\n", "2024-01-15T10:30:00\x00",
        "1000-01-01T00:00:00", "99999-01-01",
    ]:
        assert parse_timestamp(v) is None, f"expected invalid: {v!r}"

    # Size buckets — boundaries.
    assert get_size_bucket(0) == "Tiny"
    assert get_size_bucket(1) == "Tiny"
    assert get_size_bucket(64 * KIB - 1) == "Tiny"
    assert get_size_bucket(64 * KIB) == "Small"
    assert get_size_bucket(1 * MIB - 1) == "Small"
    assert get_size_bucket(1 * MIB) == "Medium"
    assert get_size_bucket(16 * MIB - 1) == "Medium"
    assert get_size_bucket(16 * MIB) == "Large"
    assert get_size_bucket(256 * MIB - 1) == "Large"
    assert get_size_bucket(256 * MIB) == "Huge"
    assert get_size_bucket(10 * GIB) == "Huge"
    # Bad input.
    assert get_size_bucket(-1) == "Unknown"
    assert get_size_bucket("nope") == "Unknown"

    # Custom thresholds.
    custom = parse_size_thresholds("1K,1M")
    assert custom is not None
    assert get_size_bucket(0, custom) == "Tiny"     # [0, 1K)
    assert get_size_bucket(1024, custom) == "Small" # [1K, 1M)
    assert get_size_bucket(MIB, custom) == "Medium" # [1M, inf)

    # Bad thresholds raise.
    for bad in ["abc", "-1", "1M,1K", "1K,,1M"]:
        try:
            parse_size_thresholds(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")

    # Layout planning.
    src = Path("/tmp/does-not-exist-xyz")
    fake = src / "report.pdf"
    # plan_relative_dir stats the file; missing file -> size 0 -> Tiny.
    assert plan_relative_dir(fake, "type", None) == Path("Documents")
    assert plan_relative_dir(fake, "size", None) == Path("Tiny")
    assert plan_relative_dir(fake, "type-size", None) == Path("Documents/Tiny")
    assert plan_relative_dir(fake, "size-type", None) == Path("Tiny/Documents")

    # Human size sanity.
    assert human_size(0).endswith("B")
    assert human_size(1024) == "1.0 KiB"
    assert human_size(1024 * 1024) == "1.0 MiB"

    # Manifest entry validation.
    assert is_valid_manifest_entry("path/to/file")
    assert is_valid_manifest_entry({"dest": "path/to/file", "timestamp": "x",
                                    "size": 10})
    assert is_valid_manifest_entry({"dest": "path/to/file"})
    assert not is_valid_manifest_entry({"dest": ""})
    assert not is_valid_manifest_entry({})
    assert not is_valid_manifest_entry(123)
    assert not is_valid_manifest_entry(None)
    assert not is_valid_manifest_entry([])

    print("Self-test passed (v4).")


# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(
        description="Organize files in a folder by category and/or size.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python document_organizer.py ~/Downloads\n"
               "  python document_organizer.py ~/Downloads --layout size\n"
               "  python document_organizer.py ~/Downloads --layout type-size\n"
               "  python document_organizer.py ~/Downloads --copy --layout size-type\n"
               "  python document_organizer.py ~/Downloads --dry-run\n"
               "  python document_organizer.py ~/Downloads --undo\n"
               "  python document_organizer.py ~/Downloads --size-thresholds 128K,2M,32M,512M\n"
               "  python document_organizer.py --self-test\n"
    )
    parser.add_argument("folder", nargs="?", help="Folder to organize")
    parser.add_argument("--copy", action="store_true",
                        help="Copy files instead of moving them")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview actions without changing anything")
    parser.add_argument("--undo", action="store_true",
                        help="Undo the last organization using the manifest")
    parser.add_argument("--layout", choices=LAYOUTS, default="type",
                        help="Folder layout strategy (default: type)")
    parser.add_argument("--size-thresholds", default=None,
                        help="Comma-separated thresholds, e.g. '64K,1M,16M,256M'")
    parser.add_argument("--self-test", action="store_true",
                        help="Run internal tests for v4 behavior")

    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    if not args.folder:
        parser.error("the following arguments are required: folder")

    source = Path(args.folder).expanduser().resolve()

    try:
        size_buckets = parse_size_thresholds(args.size_thresholds)
    except ValueError as e:
        log(f"Error: {e}")
        sys.exit(2)

    try:
        if args.undo:
            undo(source)
        else:
            moved = organize(source, copy=args.copy, dry_run=args.dry_run,
                             layout=args.layout, size_buckets=size_buckets)
            if moved and not args.dry_run:
                save_manifest(source, moved)
                log(f"Manifest saved: {MANIFEST_NAME}")
    except NotADirectoryError as e:
        log(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        log(f"Error: {e}")
        sys.exit(2)
    except KeyboardInterrupt:
        log("Interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()