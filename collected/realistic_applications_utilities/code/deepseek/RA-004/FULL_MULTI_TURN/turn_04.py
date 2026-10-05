import os
import re
import shutil
import hashlib
import mimetypes
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Size parsing / formatting
# ---------------------------------------------------------------------------

class SizeParser:
    """
    Parses human-readable size strings like '1KB', '1.5 MB', '2GiB', '0', 'inf'.
    Binary units (KiB/MiB/GiB/TiB) are 1024-based.
    Decimal units (KB/MB/GB/TB) are 1000-based by default, matching SI.
    Plain 'B' or no suffix means bytes.
    """
    
    _UNITS = {
        'b':   1,
        'kb':  1000,          'kib': 1024,
        'mb':  1000 ** 2,     'mib': 1024 ** 2,
        'gb':  1000 ** 3,     'gib': 1024 ** 3,
        'tb':  1000 ** 4,     'tib': 1024 ** 4,
        'pb':  1000 ** 5,     'pib': 1024 ** 5,
    }
    
    _PATTERN = re.compile(
        r'^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[a-zA-Z]*)\s*$'
    )
    
    @classmethod
    def parse(cls, text):
        """Parse a size string into an int number of bytes."""
        if text is None:
            raise ValueError("Size value is None")
        if isinstance(text, (int, float)):
            if text < 0:
                raise ValueError(f"Size must be non-negative, got {text}")
            return int(text)
        
        s = str(text).strip().lower()
        if s in ('inf', 'infinity', '+inf'):
            return float('inf')
        
        m = cls._PATTERN.match(s)
        if not m:
            raise ValueError(f"Unrecognized size: {text!r}")
        
        value = float(m.group('value'))
        unit = m.group('unit') or 'b'
        if unit not in cls._UNITS:
            raise ValueError(f"Unknown unit '{unit}' in {text!r}")
        
        return int(value * cls._UNITS[unit])
    
    @staticmethod
    def human(size_bytes, binary=True):
        """
        Format bytes as human-readable.
        binary=True  → KiB / MiB / GiB (1024-based, 2 decimals)
        binary=False → KB  / MB  / GB  (1000-based, 2 decimals)
        """
        if size_bytes == float('inf'):
            return 'inf'
        if size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        
        base = 1024 if binary else 1000
        units = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB') if binary \
                else ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
        
        if size_bytes < base:
            return f"{size_bytes} B"
        
        n = float(size_bytes)
        for unit in units[1:]:
            n /= base
            if n < base:
                return f"{n:.2f} {unit}"
        return f"{n:.2f} {units[-1]}"


# ---------------------------------------------------------------------------
# Size classification
# ---------------------------------------------------------------------------

class SizeClass(Enum):
    """Default named buckets. Values are the folder names used on disk."""
    TINY   = "Tiny"
    SMALL  = "Small"
    MEDIUM = "Medium"
    LARGE  = "Large"
    HUGE   = "Huge"


class SizeClassifier:
    """
    Classifies files into size buckets.
    
    Boundaries are half-open: [lower, upper). A file exactly equal to an
    upper bound falls into the next bucket. This makes the buckets
    non-overlapping and exhaustive.
    """
    
    DEFAULT_THRESHOLDS = (
        (1_024,              SizeClass.TINY),
        (1_024 ** 2,         SizeClass.SMALL),
        (100 * 1_024 ** 2,   SizeClass.MEDIUM),
        (1_024 ** 3,         SizeClass.LARGE),
        (float('inf'),       SizeClass.HUGE),
    )
    
    def __init__(self, thresholds=None, labels=None):
        """
        thresholds : iterable of (upper_bound_bytes, SizeClass)
        labels     : optional dict {SizeClass: 'folder_name'} to override
                     the folder name used for each class on disk.
        """
        self.thresholds = tuple(thresholds) if thresholds else self.DEFAULT_THRESHOLDS
        self.labels = dict(labels) if labels else {}
        self._validate()
    
    def _validate(self):
        if not self.thresholds:
            raise ValueError("At least one threshold is required")
        last = -1
        for bound, _ in self.thresholds:
            if bound == float('inf') and bound == last:
                raise ValueError("Duplicate infinity threshold")
            if bound != float('inf') and bound <= last:
                raise ValueError(
                    f"Thresholds must be strictly increasing; got {bound} after {last}"
                )
            last = bound
        if self.thresholds[-1][0] != float('inf'):
            raise ValueError("Last threshold must be float('inf')")
        
        # Every SizeClass must appear exactly once
        seen = [sc for _, sc in self.thresholds]
        if len(set(seen)) != len(seen):
            raise ValueError(f"Duplicate SizeClass in thresholds: {seen}")
    
    def classify(self, size_bytes):
        if size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        for bound, size_class in self.thresholds:
            if size_bytes < bound:
                return size_class
        return self.thresholds[-1][1]
    
    def label_for(self, size_class):
        """Folder-safe label for a size class (may be overridden)."""
        raw = self.labels.get(size_class, size_class.value)
        return sanitize_folder_name(raw)
    
    def bounds_for(self, size_class):
        """Return (lower_inclusive, upper_exclusive) in bytes for a class."""
        lower = 0
        for bound, sc in self.thresholds:
            if sc is size_class:
                return lower, bound
            if bound != float('inf'):
                lower = bound
        raise KeyError(size_class)
    
    def describe(self, size_class, binary=True):
        """Human-readable range label like '1.00 KiB – 1.00 MiB'."""
        lo, hi = self.bounds_for(size_class)
        lo_s = SizeParser.human(lo, binary=binary)
        hi_s = '∞' if hi == float('inf') else SizeParser.human(hi, binary=binary)
        return f"{lo_s} – {hi_s}"


# ---------------------------------------------------------------------------
# Path / name sanitization
# ---------------------------------------------------------------------------

_WINDOWS_RESERVED = {
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10)),
}

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_folder_name(name, fallback='Unknown'):
    """
    Turn an arbitrary label into a portable folder name.
    - Strips illegal characters
    - Collapses whitespace
    - Trims dots/spaces at ends
    - Avoids Windows reserved names
    - Enforces max length
    """
    if name is None:
        return fallback
    s = str(name).strip()
    s = _ILLEGAL_CHARS.sub('_', s)
    s = re.sub(r'\s+', ' ', s)
    s = s.strip(' .')
    if not s:
        return fallback
    if s.upper() in _WINDOWS_RESERVED:
        s = f"_{s}"
    if len(s) > 80:
        s = s[:80].rstrip(' .')
    return s


# ---------------------------------------------------------------------------
# Metadata validation
# ---------------------------------------------------------------------------

class MetadataValidator:
    MAGIC_SIGNATURES = {
        b'\xFF\xD8\xFF': {'.jpg', '.jpeg'},
        b'\x89PNG\r\n\x1a\n': {'.png'},
        b'GIF87a': {'.gif'},
        b'GIF89a': {'.gif'},
        b'BM': {'.bmp'},
        b'RIFF': {'.wav', '.avi', '.webp'},
        b'%PDF-': {'.pdf'},
        b'PK\x03\x04': {'.zip', '.docx', '.xlsx', '.pptx', '.odt', '.jar'},
        b'\x1f\x8b': {'.gz', '.tgz'},
        b'Rar!\x1a\x07': {'.rar'},
        b'7z\xbc\xaf\x27\x1c': {'.7z'},
        b'ID3': {'.mp3'},
        b'\xFF\xFB': {'.mp3'},
        b'OggS': {'.ogg'},
        b'fLaC': {'.flac'},
        b'\x00\x00\x00\x18ftyp': {'.mp4', '.m4a', '.m4v'},
        b'\x00\x00\x00\x20ftyp': {'.mp4', '.m4v'},
        b'MZ': {'.exe', '.dll'},
        b'\x7fELF': {'.so', '.o'},
    }
    
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml',
        '.html', '.htm', '.css', '.js', '.py', '.rb', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.java', '.sh', '.bat', '.ps1',
        '.log', '.ini', '.cfg', '.toml', '.env', '.sql',
    }
    
    MIN_SIZE_BYTES = 1
    MAX_SIZE_BYTES = 50 * 1024 ** 3
    
    def __init__(self, strict=False, check_magic=True, check_archive=True,
                 check_hash=True, max_size=MAX_SIZE_BYTES):
        self.strict = strict
        self.check_magic = check_magic
        self.check_archive = check_archive
        self.check_hash = check_hash
        self.max_size = max_size
        self._hash_cache = {}
    
    def validate(self, file_path):
        issues = []
        metadata = {}
        
        try:
            stat = file_path.stat()
        except (OSError, FileNotFoundError) as e:
            return False, [f"Cannot stat file: {e}"], {}
        
        metadata['size_bytes'] = stat.st_size
        if stat.st_size < self.MIN_SIZE_BYTES:
            issues.append(f"File is empty (size={stat.st_size})")
        if stat.st_size > self.max_size:
            issues.append(
                f"File exceeds max size ({SizeParser.human(stat.st_size)})"
            )
        
        now = datetime.now().timestamp()
        metadata['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        metadata['created'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
        if stat.st_mtime > now + 86400:
            issues.append("Modification time is in the future")
        
        ext = file_path.suffix.lower()
        metadata['extension'] = ext
        if not ext:
            issues.append("File has no extension")
        
        guessed_mime, _ = mimetypes.guess_type(file_path.name)
        metadata['mime_guess'] = guessed_mime or 'unknown'
        
        if self.check_magic and ext and stat.st_size > 0:
            issue = self._check_magic_bytes(file_path, ext)
            if issue:
                issues.append(issue)
        
        if self.check_archive and ext in {'.zip', '.docx', '.xlsx', '.pptx',
                                          '.odt', '.jar', '.tar', '.gz', '.tgz'}:
            issue = self._check_archive(file_path, ext)
            if issue:
                issues.append(issue)
        
        if not os.access(file_path, os.R_OK):
            issues.append("File is not readable")
        
        if self.check_hash:
            digest = self._compute_hash(file_path)
            if digest is None:
                issues.append("Could not compute hash (unreadable or vanished)")
            else:
                metadata['sha256'] = digest
        
        name_issue = self._check_filename(file_path.name)
        if name_issue:
            issues.append(name_issue)
        
        return len(issues) == 0, issues, metadata
    
    def _check_magic_bytes(self, file_path, ext):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
        except OSError as e:
            return f"Cannot read header: {e}"
        
        if ext in self.TEXT_EXTENSIONS:
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                if b'\x00' in chunk:
                    return f"File .{ext.lstrip('.')} contains NUL bytes (expected text)"
            except OSError:
                pass
            return None
        
        matched = None
        for sig, exts in self.MAGIC_SIGNATURES.items():
            if header.startswith(sig):
                matched = exts
                break
        
        if matched is None:
            if self.strict and ext not in self.TEXT_EXTENSIONS:
                return f"No recognized magic bytes for '{ext}' (strict mode)"
            return None
        if ext not in matched:
            return (f"Extension '{ext}' does not match file content "
                    f"(expected one of {sorted(matched)})")
        return None
    
    def _check_archive(self, file_path, ext):
        try:
            if ext in {'.zip', '.docx', '.xlsx', '.pptx', '.odt', '.jar'}:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    bad = zf.testzip()
                    if bad is not None:
                        return f"Corrupt entry in zip: {bad}"
            elif ext == '.tar':
                with tarfile.open(file_path, 'r:*') as tf:
                    for _ in tf:
                        pass
            elif ext in {'.gz', '.tgz'}:
                opener = (tarfile.open(file_path, 'r:gz') if ext == '.tgz'
                          else __import__('gzip').open(file_path, 'rb'))
                with opener as f:
                    f.read(1024)
        except Exception as e:
            return f"Archive integrity check failed: {type(e).__name__}: {e}"
        return None
    
    def _check_filename(self, name):
        if len(name) > 255:
            return f"Filename too long ({len(name)} chars)"
        if name != name.strip():
            return "Filename has leading/trailing whitespace"
        if any(c in name for c in '<>:"|?*'):
            return "Filename contains reserved characters"
        if name.startswith('.'):
            return "File is hidden"
        return None
    
    def _compute_hash(self, file_path, chunk_size=1 << 20):
        try:
            st = file_path.stat()
        except OSError:
            return None
        key = (str(file_path), st.st_mtime, st.st_size)
        if key in self._hash_cache:
            return self._hash_cache[key]
        h = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b''):
                    h.update(chunk)
        except OSError:
            return None
        digest = h.hexdigest()
        self._hash_cache[key] = digest
        return digest


# ---------------------------------------------------------------------------
# Organizer
# ---------------------------------------------------------------------------

class FileOrganizer:
    """
    Organizes files with metadata validation and size classification.
    
    size_mode:
      'off'    – flat by category; size recorded but not used for routing.
      'subdir' – <Category>/<SizeLabel>/
      'top'    – <SizeLabel>/<Category>/
    
    Boundary semantics:
      Buckets are [lower, upper). A file whose size equals an upper bound
      belongs to the next bucket. 'off' mode does not affect the folder
      structure but still records the classification.
    """
    
    CATEGORIES = {
        '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images',
        '.bmp': 'Images', '.svg': 'Images', '.webp': 'Images', '.ico': 'Images',
        '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
        '.txt': 'Documents', '.rtf': 'Documents', '.odt': 'Documents',
        '.xls': 'Documents', '.xlsx': 'Documents', '.csv': 'Documents',
        '.ppt': 'Documents', '.pptx': 'Documents', '.md': 'Documents',
        '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.aac': 'Audio',
        '.ogg': 'Audio', '.m4a': 'Audio', '.wma': 'Audio',
        '.mp4': 'Video', '.avi': 'Video', '.mkv': 'Video', '.mov': 'Video',
        '.wmv': 'Video', '.flv': 'Video', '.webm': 'Video', '.m4v': 'Video',
        '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives',
        '.tar': 'Archives', '.gz': 'Archives', '.bz2': 'Archives',
        '.py': 'Code', '.js': 'Code', '.html': 'Code', '.css': 'Code',
        '.java': 'Code', '.cpp': 'Code', '.c': 'Code', '.h': 'Code',
        '.json': 'Code', '.xml': 'Code', '.yaml': 'Code', '.yml': 'Code',
        '.sh': 'Code', '.rb': 'Code', '.go': 'Code', '.rs': 'Code',
        '.exe': 'Executables', '.msi': 'Executables', '.app': 'Executables',
        '.deb': 'Executables', '.rpm': 'Executables', '.dmg': 'Executables',
    }
    
    OTHER_FOLDER = 'Other'
    QUARANTINE_FOLDER = '_Quarantine'
    LOG_FILE = 'organizer_log.txt'
    
    SIZE_MODES = ('off', 'subdir', 'top')
    
    def __init__(self, target_dir, dry_run=False, recursive=False,
                 validate=True, strict=False, quarantine=False,
                 skip_duplicates=True,
                 size_mode='off', size_thresholds=None, size_labels=None,
                 binary_units=True):
        self.target_dir = Path(target_dir).resolve()
        self.dry_run = dry_run
        self.recursive = recursive
        self.quarantine = quarantine
        self.skip_duplicates = skip_duplicates
        self.binary_units = binary_units
        
        self.validator = MetadataValidator(strict=strict) if validate else None
        self.size_classifier = SizeClassifier(
            thresholds=size_thresholds, labels=size_labels,
        )
        
        if size_mode not in self.SIZE_MODES:
            raise ValueError(
                f"size_mode must be one of {self.SIZE_MODES}, got {size_mode!r}"
            )
        self.size_mode = size_mode
        
        self.moved = []
        self.skipped = []
        self.errors = []
        self.invalid = []
        self.duplicates = []
        self._seen_hashes = {}
        
        if not self.target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.target_dir}")
        if not self.target_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.target_dir}")
    
    def _get_category(self, file_path):
        cat = self.CATEGORIES.get(file_path.suffix.lower(), self.OTHER_FOLDER)
        return sanitize_folder_name(cat)
    
    def _build_destination_dir(self, category, size_class):
        base = self.target_dir
        if self.size_mode == 'off':
            return base / category
        label = self.size_classifier.label_for(size_class)
        if self.size_mode == 'subdir':
            return base / category / label
        if self.size_mode == 'top':
            return base / label / category
        raise RuntimeError(f"Unknown size_mode: {self.size_mode}")
    
    def _unique_destination(self, dest_path):
        if not dest_path.exists():
            return dest_path
        stem, suffix = dest_path.stem, dest_path.suffix
        counter = 1
        while True:
            candidate = dest_path.with_name(f"{stem} ({counter}){suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
    
    def _managed_top_level_names(self):
        names = set(self.CATEGORIES.values()) | {
            self.OTHER_FOLDER, self.QUARANTINE_FOLDER,
        }
        # Size labels may be custom, so collect every label in use
        for _, sc in self.size_classifier.thresholds:
            names.add(self.size_classifier.label_for(sc))
        return names
    
    def _iter_files(self):
        managed = self._managed_top_level_names()
        pattern = '**/*' if self.recursive else '*'
        for entry in self.target_dir.glob(pattern):
            if not entry.is_file():
                continue
            if entry.name == self.LOG_FILE:
                continue
            rel_parts = entry.relative_to(self.target_dir).parts[:-1]
            if any(part in managed for part in rel_parts):
                continue
            yield entry
    
    def _handle_invalid(self, file_path, issues):
        self.invalid.append((file_path, issues))
        if self.quarantine and not self.dry_run:
            qdir = self.target_dir / self.QUARANTINE_FOLDER
            qdir.mkdir(exist_ok=True)
            dest = self._unique_destination(qdir / file_path.name)
            try:
                shutil.move(str(file_path), str(dest))
                with open(dest.with_suffix(dest.suffix + '.reason.txt'),
                          'w', encoding='utf-8') as f:
                    f.write("Quarantined by FileOrganizer\n")
                    f.write(f"Original: {file_path}\n")
                    f.write(f"When: {datetime.now().isoformat()}\n")
                    f.write("Issues:\n")
                    for issue in issues:
                        f.write(f"  - {issue}\n")
                print(f"  QUARANTINED: {file_path.name} ({len(issues)} issues)")
            except Exception as e:
                self.errors.append((file_path, f"Quarantine failed: {e}"))
                print(f"  ERROR quarantining {file_path.name}: {e}")
        else:
            print(f"  INVALID: {file_path.name} — {'; '.join(issues)}")
    
    def organize(self):
        header = '[DRY RUN] ' if self.dry_run else ''
        print(f"{header}Organizing: {self.target_dir}")
        print(f"Size mode: {self.size_mode}")
        print(f"Units:     {'binary (1024)' if self.binary_units else 'decimal (1000)'}")
        print("Buckets:")
        for bound, sc in self.size_classifier.thresholds:
            lo, hi = self.size_classifier.bounds_for(sc)
            lo_s = SizeParser.human(lo, binary=self.binary_units)
            hi_s = ('∞' if hi == float('inf')
                    else SizeParser.human(hi, binary=self.binary_units))
            print(f"  {self.size_classifier.label_for(sc):<10} "
                  f"[{lo_s}, {hi_s})")
        print()
        
        for file_path in self._iter_files():
            metadata = {}
            if self.validator is not None:
                is_valid, issues, metadata = self.validator.validate(file_path)
                if not is_valid:
                    self._handle_invalid(file_path, issues)
                    continue
            
            size_bytes = metadata.get('size_bytes')
            if size_bytes is None:
                try:
                    size_bytes = file_path.stat().st_size
                except OSError:
                    size_bytes = 0
            size_class = self.size_classifier.classify(size_bytes)
            label = self.size_classifier.label_for(size_class)
            metadata['size_bytes'] = size_bytes
            metadata['size_class'] = size_class.value
            metadata['size_label'] = label
            metadata['size_human'] = SizeParser.human(
                size_bytes, binary=self.binary_units
            )
            metadata['size_bounds'] = self.size_classifier.describe(
                size_class, binary=self.binary_units
            )
            
            digest = metadata.get('sha256')
            if digest and self.skip_duplicates and digest in self._seen_hashes:
                original = self._seen_hashes[digest]
                self.duplicates.append((file_path, original))
                print(f"  DUPLICATE: {file_path.name} (matches {original.name})")
                continue
            if digest:
                self._seen_hashes[digest] = file_path
            
            category = self._get_category(file_path)
            dest_dir = self._build_destination_dir(category, size_class)
            dest = self._unique_destination(dest_dir / file_path.name)
            
            try:
                if not self.dry_run:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest))
                self.moved.append((file_path, dest, category, metadata))
                try:
                    display = dest.parent.relative_to(self.target_dir)
                except ValueError:
                    display = dest.parent
                print(f"  {'WOULD MOVE' if self.dry_run else 'MOVED'}: "
                      f"{file_path.name} "
                      f"[{label}, {metadata['size_human']}] "
                      f"-> {display}/")
            except Exception as e:
                self.errors.append((file_path, str(e)))
                print(f"  ERROR: {file_path.name} - {e}")
        
        self._write_log()
        self._print_summary()
    
    def _write_log(self):
        if self.dry_run:
            return
        log_path = self.target_dir / self.LOG_FILE
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n--- Run: {datetime.now().isoformat()} ---\n")
            f.write(f"Size mode: {self.size_mode}\n")
            f.write(f"Units: {'binary' if self.binary_units else 'decimal'}\n")
            for src, dst, cat, meta in self.moved:
                sha = meta.get('sha256', '')
                f.write(f"MOVED [{meta.get('size_label','?')}, "
                        f"{meta.get('size_human','?')}, "
                        f"bounds={meta.get('size_bounds','?')}] "
                        f"{src} -> {dst}  sha256={sha[:16]}...\n")
            for src, issues in self.invalid:
                f.write(f"INVALID {src}: {'; '.join(issues)}\n")
            for src, orig in self.duplicates:
                f.write(f"DUPLICATE {src} (of {orig})\n")
            for src, err in self.errors:
                f.write(f"ERROR {src}: {err}\n")
    
    def _print_summary(self):
        print(f"\n{'=' * 56}")
        print(f"Summary{' (DRY RUN)' if self.dry_run else ''}")
        print(f"{'=' * 56}")
        print(f"  Moved:      {len(self.moved)}")
        print(f"  Invalid:    {len(self.invalid)}")
        print(f"  Duplicates: {len(self.duplicates)}")
        print(f"  Errors:     {len(self.errors)}")
        
        if not self.moved:
            return
        
        by_cat = {}
        total_bytes = 0
        for _, _, cat, meta in self.moved:
            by_cat[cat] = by_cat.get(cat, 0) + 1
            total_bytes += meta.get('size_bytes', 0)
        print("\n  By category:")
        for cat, count in sorted(by_cat.items()):
            print(f"    {cat}: {count}")
        
        # --- Size distribution, in threshold order, with boundaries ---
        by_size = {}
        bytes_by_size = {}
        for _, _, _, meta in self.moved:
            sc = meta.get('size_class', 'Unknown')
            by_size[sc] = by_size.get(sc, 0) + 1
            bytes_by_size[sc] = bytes_by_size.get(sc, 0) + meta.get('size_bytes', 0)
        
        print("\n  By size class:")
        for _, sc in self.size_classifier.thresholds:
            label = self.size_classifier.label_for(sc)
            n = by_size.get(sc.value, 0)
            b = bytes_by_size.get(sc.value, 0)
            lo, hi = self.size_classifier.bounds_for(sc)
            lo_s = SizeParser.human(lo, binary=self.binary_units)
            hi_s = ('∞' if hi == float('inf')
                    else SizeParser.human(hi, binary=self.binary_units))
            bar = '█' * min(n, 30) if n else ''
            b_s = SizeParser.human(b, binary=self.binary_units)
            print(f"    {label:<10} [{lo_s:>9} – {hi_s:>9})  "
                  f"{n:>4}  ({b_s:>10})  {bar}")
        
        print(f"\n  Total size: {SizeParser.human(total_bytes, binary=self.binary_units)}")
        
        # --- Boundary edge cases hint ---
        print("\n  Note: bounds are half-open [lo, hi). A file exactly")
        print("        equal to an upper bound lands in the next bucket.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_label_overrides(pairs):
    """Parse 'Tiny=t,Small=s,Medium=m,Large=L,Huge=H' into {SizeClass: label}."""
    result = {}
    if not pairs:
        return result
    for piece in pairs.split(','):
        if '=' not in piece:
            raise ValueError(f"Bad label override (expected Class=Name): {piece!r}")
        key, val = piece.split('=', 1)
        key = key.strip()
        try:
            sc = SizeClass[key.upper()]
        except KeyError:
            raise ValueError(
                f"Unknown size class {key!r}; valid: "
                f"{[s.name for s in SizeClass]}"
            )
        result[sc] = val.strip()
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Organize files with metadata validation and '
                    'configurable size classification.')
    parser.add_argument('directory', help='Directory to organize')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--recursive', action='store_true')
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--quarantine', action='store_true')
    parser.add_argument('--no-validate', action='store_true')
    parser.add_argument('--allow-duplicates', action='store_true')
    
    parser.add_argument('--size-mode', choices=FileOrganizer.SIZE_MODES,
                        default='off',
                        help="'off', 'subdir' (<Cat>/<Size>/) or 'top' (<Size>/<Cat>/)")
    parser.add_argument('--decimal', action='store_true',
                        help='Use decimal units (1000-based) for display and parsing')
    parser.add_argument('--tiny-max',   default='1KiB')
    parser.add_argument('--small-max',  default='1MiB')
    parser.add_argument('--medium-max', default='100MiB')
    parser.add_argument('--large-max',  default='1GiB')
    parser.add_argument('--labels', default=None,
                        help="Override folder labels, e.g. "
                             "'Tiny=t,Small=s,Medium=m,Large=L,Huge=H'")
    
    args = parser.parse_args()
    
    binary = not args.decimal
    unit_scale = 1 if binary else 1000 / 1024  # n/a — parser handles units
    
    # Parse thresholds; if user gave plain numbers, treat them as bytes.
    tiny   = SizeParser.parse(args.tiny_max)
    small  = SizeParser.parse(args.small_max)
    medium = SizeParser.parse(args.medium_max)
    large  = SizeParser.parse(args.large_max)
    
    thresholds = (
        (tiny,   SizeClass.TINY),
        (small,  SizeClass.SMALL),
        (medium, SizeClass.MEDIUM),
        (large,  SizeClass.LARGE),
        (float('inf'), SizeClass.HUGE),
    )
    
    labels = _parse_label_overrides(args.labels)
    
    organizer = FileOrganizer(
        args.directory,
        dry_run=args.dry_run,
        recursive=args.recursive,
        validate=not args.no_validate,
        strict=args.strict,
        quarantine=args.quarantine,
        skip_duplicates=not args.allow_duplicates,
        size_mode=args.size_mode,
        size_thresholds=thresholds,
        size_labels=labels,
        binary_units=binary,
    )
    organizer.organize()