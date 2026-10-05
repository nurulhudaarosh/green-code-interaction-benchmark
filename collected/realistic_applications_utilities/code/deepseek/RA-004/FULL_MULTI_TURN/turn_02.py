import os
import shutil
import hashlib
import mimetypes
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime

class MetadataValidator:
    """Validates file metadata before organization."""
    
    # Extensions with known magic-byte signatures
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
    
    # Text-based extensions (no magic bytes expected)
    TEXT_EXTENSIONS = {
        '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml',
        '.html', '.htm', '.css', '.js', '.py', '.rb', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.java', '.sh', '.bat', '.ps1',
        '.log', '.ini', '.cfg', '.toml', '.env', '.sql',
    }
    
    MIN_SIZE_BYTES = 1
    MAX_SIZE_BYTES = 50 * 1024 ** 3  # 50 GB
    
    def __init__(self, strict=False, check_magic=True, check_archive=True,
                 check_hash=True, max_size=MAX_SIZE_BYTES):
        self.strict = strict
        self.check_magic = check_magic
        self.check_archive = check_archive
        self.check_hash = check_hash
        self.max_size = max_size
        self._hash_cache = {}
    
    def validate(self, file_path):
        """Return (is_valid, list_of_issues, metadata_dict)."""
        issues = []
        metadata = {}
        
        try:
            stat = file_path.stat()
        except (OSError, FileNotFoundError) as e:
            return False, [f"Cannot stat file: {e}"], {}
        
        # --- Size checks ---
        metadata['size_bytes'] = stat.st_size
        if stat.st_size < self.MIN_SIZE_BYTES:
            issues.append(f"File is empty (size={stat.st_size})")
        if stat.st_size > self.max_size:
            issues.append(f"File exceeds max size ({self._human(stat.st_size)})")
        
        # --- Timestamp checks ---
        now = datetime.now().timestamp()
        metadata['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        metadata['created'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
        if stat.st_mtime > now + 86400:
            issues.append("Modification time is in the future")
        
        # --- Extension / MIME checks ---
        ext = file_path.suffix.lower()
        metadata['extension'] = ext
        
        if not ext:
            issues.append("File has no extension")
        
        guessed_mime, _ = mimetypes.guess_type(file_path.name)
        metadata['mime_guess'] = guessed_mime or 'unknown'
        
        # --- Magic byte check ---
        if self.check_magic and ext and stat.st_size > 0:
            magic_issue = self._check_magic_bytes(file_path, ext)
            if magic_issue:
                issues.append(magic_issue)
        
        # --- Archive integrity check ---
        if self.check_archive and ext in {'.zip', '.docx', '.xlsx', '.pptx',
                                          '.odt', '.jar', '.tar', '.gz', '.tgz'}:
            archive_issue = self._check_archive(file_path, ext)
            if archive_issue:
                issues.append(archive_issue)
        
        # --- Readable check ---
        if not os.access(file_path, os.R_OK):
            issues.append("File is not readable")
        
        # --- Hash (for duplicate detection later) ---
        if self.check_hash:
            digest = self._compute_hash(file_path)
            if digest is None:
                issues.append("Could not compute hash (unreadable or vanished)")
            else:
                metadata['sha256'] = digest
        
        # --- Filename sanity ---
        name_issue = self._check_filename(file_path.name)
        if name_issue:
            issues.append(name_issue)
        
        is_valid = len(issues) == 0
        return is_valid, issues, metadata
    
    # ----- Internal helpers -----
    
    def _check_magic_bytes(self, file_path, ext):
        """Verify file header matches expected signature for its extension."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(16)
        except OSError as e:
            return f"Cannot read header: {e}"
        
        # Skip check for known text formats
        if ext in self.TEXT_EXTENSIONS:
            # Light sanity: text files shouldn't contain NUL in first 8KB
            try:
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                if b'\x00' in chunk:
                    return f"File .{ext.lstrip('.')} contains NUL bytes (expected text)"
            except OSError:
                pass
            return None
        
        # Look for a matching signature
        matched_exts = None
        for sig, exts in self.MAGIC_SIGNATURES.items():
            if header.startswith(sig):
                matched_exts = exts
                break
        
        if matched_exts is None:
            # No known signature — only flag in strict mode
            if self.strict and ext not in self.TEXT_EXTENSIONS:
                return f"No recognized magic bytes for '{ext}' (strict mode)"
            return None
        
        if ext not in matched_exts:
            return (f"Extension '{ext}' does not match file content "
                    f"(expected one of {sorted(matched_exts)})")
        
        return None
    
    def _check_archive(self, file_path, ext):
        """Test archive integrity without extracting."""
        try:
            if ext in {'.zip', '.docx', '.xlsx', '.pptx', '.odt', '.jar'}:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    bad = zf.testzip()
                    if bad is not None:
                        return f"Corrupt entry in zip: {bad}"
            elif ext in {'.tar'}:
                with tarfile.open(file_path, 'r:*') as tf:
                    # Just force reading headers
                    for _ in tf:
                        pass
            elif ext in {'.gz', '.tgz'}:
                with tarfile.open(file_path, 'r:gz') if ext == '.tgz' else \
                     __import__('gzip').open(file_path, 'rb') as f:
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
            return "File is hidden"  # informational, not fatal
        return None
    
    def _compute_hash(self, file_path, chunk_size=1 << 20):
        """SHA-256 in a streaming fashion."""
        key = (str(file_path), file_path.stat().st_mtime, file_path.stat().st_size)
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
    
    @staticmethod
    def _human(n):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"


class FileOrganizer:
    """Organizes files with metadata validation before moving."""
    
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
    
    def __init__(self, target_dir, dry_run=False, recursive=False,
                 validate=True, strict=False, quarantine=False,
                 skip_duplicates=True):
        self.target_dir = Path(target_dir).resolve()
        self.dry_run = dry_run
        self.recursive = recursive
        self.quarantine = quarantine
        self.skip_duplicates = skip_duplicates
        
        self.validator = MetadataValidator(strict=strict) if validate else None
        
        self.moved = []
        self.skipped = []
        self.errors = []
        self.invalid = []
        self.duplicates = []
        self._seen_hashes = {}  # sha256 -> path of first occurrence
        
        if not self.target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.target_dir}")
        if not self.target_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.target_dir}")
    
    def _get_category(self, file_path):
        return self.CATEGORIES.get(file_path.suffix.lower(), self.OTHER_FOLDER)
    
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
    
    def _iter_files(self):
        category_names = (set(self.CATEGORIES.values())
                          | {self.OTHER_FOLDER, self.QUARANTINE_FOLDER})
        pattern = '**/*' if self.recursive else '*'
        for entry in self.target_dir.glob(pattern):
            if not entry.is_file():
                continue
            if entry.name == self.LOG_FILE:
                continue
            rel_parts = entry.relative_to(self.target_dir).parts[:-1]
            if any(part in category_names for part in rel_parts):
                continue
            yield entry
    
    def _handle_invalid(self, file_path, issues):
        """Route an invalid file — either quarantine or skip."""
        self.invalid.append((file_path, issues))
        if self.quarantine and not self.dry_run:
            qdir = self.target_dir / self.QUARANTINE_FOLDER
            qdir.mkdir(exist_ok=True)
            dest = self._unique_destination(qdir / file_path.name)
            try:
                shutil.move(str(file_path), str(dest))
                # Sidecar note explaining why
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
        print(f"{header}Organizing: {self.target_dir}\n")
        
        for file_path in self._iter_files():
            # ---- Validation phase ----
            metadata = {}
            if self.validator is not None:
                is_valid, issues, metadata = self.validator.validate(file_path)
                if not is_valid:
                    self._handle_invalid(file_path, issues)
                    continue
            
            # ---- Duplicate detection ----
            digest = metadata.get('sha256')
            if digest and self.skip_duplicates and digest in self._seen_hashes:
                original = self._seen_hashes[digest]
                self.duplicates.append((file_path, original))
                print(f"  DUPLICATE: {file_path.name} (matches {original.name})")
                continue
            if digest:
                self._seen_hashes[digest] = file_path
            
            # ---- Move phase ----
            category = self._get_category(file_path)
            category_dir = self.target_dir / category
            dest = self._unique_destination(category_dir / file_path.name)
            
            try:
                if not self.dry_run:
                    category_dir.mkdir(exist_ok=True)
                    shutil.move(str(file_path), str(dest))
                self.moved.append((file_path, dest, category, metadata))
                size = metadata.get('size_bytes')
                size_str = f" ({MetadataValidator._human(size)})" if size else ""
                print(f"  {'WOULD MOVE' if self.dry_run else 'MOVED'}: "
                      f"{file_path.name}{size_str} -> {category}/")
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
            for src, dst, cat, meta in self.moved:
                sha = meta.get('sha256', '')
                f.write(f"MOVED {src} -> {dst}  sha256={sha[:16]}...\n")
            for src, issues in self.invalid:
                f.write(f"INVALID {src}: {'; '.join(issues)}\n")
            for src, orig in self.duplicates:
                f.write(f"DUPLICATE {src} (of {orig})\n")
            for src, err in self.errors:
                f.write(f"ERROR {src}: {err}\n")
    
    def _print_summary(self):
        print(f"\n{'=' * 40}")
        print(f"Summary{' (DRY RUN)' if self.dry_run else ''}")
        print(f"{'=' * 40}")
        print(f"  Moved:      {len(self.moved)}")
        print(f"  Invalid:    {len(self.invalid)}")
        print(f"  Duplicates: {len(self.duplicates)}")
        print(f"  Errors:     {len(self.errors)}")
        
        if self.moved:
            by_cat = {}
            total_bytes = 0
            for _, _, cat, meta in self.moved:
                by_cat[cat] = by_cat.get(cat, 0) + 1
                total_bytes += meta.get('size_bytes', 0)
            print("\n  By category:")
            for cat, count in sorted(by_cat.items()):
                print(f"    {cat}: {count}")
            print(f"\n  Total size: {MetadataValidator._human(total_bytes)}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize files with metadata validation.')
    parser.add_argument('directory', help='Directory to organize')
    parser.add_argument('--dry-run', action='store_true', help='Preview without moving')
    parser.add_argument('--recursive', action='store_true', help='Include subdirectories')
    parser.add_argument('--strict', action='store_true',
                        help='Flag files whose content lacks a recognized signature')
    parser.add_argument('--quarantine', action='store_true',
                        help='Move invalid files into _Quarantine/ instead of skipping')
    parser.add_argument('--no-validate', action='store_true',
                        help='Disable metadata validation entirely')
    parser.add_argument('--allow-duplicates', action='store_true',
                        help='Do not skip files with duplicate content')
    args = parser.parse_args()
    
    organizer = FileOrganizer(
        args.directory,
        dry_run=args.dry_run,
        recursive=args.recursive,
        validate=not args.no_validate,
        strict=args.strict,
        quarantine=args.quarantine,
        skip_duplicates=not args.allow_duplicates,
    )
    organizer.organize()