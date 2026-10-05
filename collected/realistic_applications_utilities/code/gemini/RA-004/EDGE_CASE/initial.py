import hashlib
import json
import logging
import os
import shutil
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DocumentOrganizer:
    """
    A complete, robust document organization tool that automatically scans,
    categorizes, renames, deduplicates, and moves files into a structured directory tree.
    
    Handles:
    - Missing/empty extensions and hidden dotfiles (.gitignore, .env).
    - Complex file/extension separators and trailing whitespace/dots.
    - Missing or empty filenames.
    - Exact upper/lower size boundary edge cases.
    - Safe date parsing for malformed or out-of-bounds file metadata.
    """

    DEFAULT_CATEGORY_RULES = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"],
        "Documents": [".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt", ".tex"],
        "Spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
        "Presentations": [".pptx", ".ppt", ".key", ".odp"],
        "Audio": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"],
        "Video": [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv"],
        "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".tar.gz", ".tgz"],
        "Code": [".py", ".js", ".html", ".css", ".cpp", ".c", ".java", ".json", ".xml", ".sh"],
        "Executable": [".exe", ".dmg", ".pkg", ".deb", ".msi"]
    }

    # Size-bucket thresholds in bytes using precise half-open intervals [min_bytes, max_bytes)
    SIZE_BUCKETS = {
        "Tiny (<1MB)": (0, 1 * 1024 * 1024),
        "Small (1MB-10MB)": (1 * 1024 * 1024, 10 * 1024 * 1024),
        "Medium (10MB-100MB)": (10 * 1024 * 1024, 100 * 1024 * 1024),
        "Large (100MB-1GB)": (100 * 1024 * 1024, 1024 * 1024 * 1024),
        "Huge (>=1GB)": (1024 * 1024 * 1024, float("inf")),
    }

    def __init__(self, target_dir: str, rules: Optional[Dict[str, List[str]]] = None):
        self.target_dir = Path(target_dir).resolve()
        self.rules = rules or self.DEFAULT_CATEGORY_RULES
        self.ext_to_category = self._build_extension_map()

    def _build_extension_map(self) -> Dict[str, str]:
        """Maps each normalized extension (lowercased, leading dot) to its category."""
        ext_map = {}
        for category, extensions in self.rules.items():
            for ext in extensions:
                cleaned_ext = ext.strip().lower()
                if not cleaned_ext.startswith('.'):
                    cleaned_ext = f".{cleaned_ext}"
                ext_map[cleaned_ext] = category
        return ext_map

    def _extract_extension_and_stem(self, file_path: Path) -> tuple[str, str]:
        """
        Handles missing extensions, custom separators, trailing dot/spaces,
        dotfiles, and empty filenames safely. Returns (extension, stem).
        """
        # Strip outer whitespace and trailing dots/separators
        raw_name = file_path.name.strip().rstrip('. ')

        # Handle empty filename edge-cases (e.g., file named "   " or "...")
        if not raw_name:
            return "", "unnamed_file"

        # Handle dotfiles / hidden files without explicit extension (e.g., `.env`, `.gitignore`)
        if raw_name.startswith('.') and raw_name.count('.') == 1:
            return "", raw_name

        p = Path(raw_name)
        suffixes = [s.lower() for s in p.suffixes]

        # Check multi-part compound extensions (e.g. .tar.gz, .backup.pdf)
        if len(suffixes) >= 2:
            compound_ext = "".join(suffixes[-2:])
            if compound_ext in self.ext_to_category:
                stem = raw_name[:-len(compound_ext)]
                return compound_ext, stem if stem else "unnamed_file"

        # Fall back to single suffix
        if suffixes:
            ext = suffixes[-1]
            stem = raw_name[:-len(ext)]
            return ext, stem if stem else "unnamed_file"

        # No extension present
        return "", raw_name

    def get_category(self, file_path: Path) -> str:
        """Determines category based on extension, MIME type, or fallback."""
        ext, _ = self._extract_extension_and_stem(file_path)
        if ext and ext in self.ext_to_category:
            return self.ext_to_category[ext]

        # MIME type fallback
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            main_type = mime_type.split("/")[0].capitalize()
            if main_type in ["Image", "Audio", "Video", "Text"]:
                return main_type

        return "No Extension" if not ext else "Others"

    def get_size_bucket(self, file_path: Path) -> str:
        """
        Classifies the file into exact size buckets.
        Strictly handles exact byte boundaries (e.g., exactly 1,048,576 bytes -> Small).
        """
        try:
            file_size = file_path.stat().st_size
        except OSError:
            return "Unknown Size"

        # Special check for empty zero-byte files
        if file_size == 0:
            return "Empty (0 Bytes)"

        for bucket_name, (min_bytes, max_bytes) in self.SIZE_BUCKETS.items():
            if min_bytes <= file_size < max_bytes:
                return bucket_name

        return "Unknown Size"

    def _get_safe_modification_date(self, file_path: Path) -> datetime:
        """Safely handles OS-level timestamp errors and falls back to current time."""
        try:
            mtime = file_path.stat().st_mtime
            if mtime < 0 or mtime > 253402300799:
                raise ValueError("Timestamp out of valid datetime range.")
            return datetime.fromtimestamp(mtime)
        except (OSError, ValueError, OverflowError) as e:
            logging.warning(f"Malformed date metadata for {file_path.name} ({e}). Falling back to current date.")
            return datetime.now()

    @staticmethod
    def calculate_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
        """Calculates SHA256 hash for exact duplicate detection."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    def organize(
        self,
        move_files: bool = True,
        remove_duplicates: bool = False,
        date_folders: bool = False,
        size_folders: bool = False
    ) -> Dict[str, List[str]]:
        """
        Executes complete document organization with safe handling for missing extensions,
        separators, empty names, exact size boundaries, and malformed dates.
        """
        if not self.target_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.target_dir}")

        seen_hashes: Dict[str, Path] = {}
        report = {"moved": [], "duplicates_removed": [], "skipped": [], "errors": []}

        try:
            files = [f for f in self.target_dir.rglob("*") if f.is_file()]
        except Exception as e:
            logging.error(f"Failed to scan directory: {e}")
            return report

        for file_path in files:
            try:
                # Prevent re-organizing files in already managed category folders
                if file_path.parent.name in self.rules.keys() or file_path.parent.name in ["Others", "No Extension"]:
                    continue

                if remove_duplicates:
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash in seen_hashes:
                        logging.info(f"Duplicate detected: Removing {file_path.name}")
                        file_path.unlink()
                        report["duplicates_removed"].append(str(file_path))
                        continue
                    seen_hashes[file_hash] = file_path

                category = self.get_category(file_path)
                dest_dir = self.target_dir / category

                if size_folders:
                    size_bucket = self.get_size_bucket(file_path)
                    dest_dir = dest_dir / size_bucket

                if date_folders:
                    file_date = self._get_safe_modification_date(file_path)
                    dest_dir = dest_dir / f"{file_date.year}" / f"{file_date.strftime('%m-%B')}"

                dest_dir.mkdir(parents=True, exist_ok=True)

                # Robust extension and stem extraction for collision-free renaming
                ext, stem = self._extract_extension_and_stem(file_path)
                target_filename = f"{stem}{ext}"
                dest_file_path = dest_dir / target_filename

                counter = 1
                while dest_file_path.exists():
                    dest_file_path = dest_dir / f"{stem}_{counter}{ext}"
                    counter += 1

                if move_files:
                    shutil.move(str(file_path), str(dest_file_path))
                else:
                    shutil.copy2(str(file_path), str(dest_file_path))

                logging.info(f"Organized: {file_path.name} -> {dest_file_path}")
                report["moved"].append(f"{file_path.name} -> {dest_file_path}")

            except Exception as err:
                logging.error(f"Error processing {file_path.name}: {err}")
                report["errors"].append(f"{file_path.name}: {str(err)}")

        return report


# Usage Example
if __name__ == "__main__":
    organizer = DocumentOrganizer(target_dir="./sample_documents")
    # summary = organizer.organize(move_files=True, remove_duplicates=True, date_folders=True, size_folders=True)
    # print(json.dumps(summary, indent=4))