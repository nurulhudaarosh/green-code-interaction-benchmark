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
    Supports extension normalization, safe malformed-date fallback, and size-bucket classification.
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

    # Size-bucket thresholds in bytes
    SIZE_BUCKETS = {
        "Tiny (<1MB)": (0, 1 * 1024 * 1024),
        "Small (1MB-10MB)": (1 * 1024 * 1024, 10 * 1024 * 1024),
        "Medium (10MB-100MB)": (10 * 1024 * 1024, 100 * 1024 * 1024),
        "Large (100MB-1GB)": (100 * 1024 * 1024, 1024 * 1024 * 1024),
        "Huge (>1GB)": (1024 * 1024 * 1024, float("inf")),
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

    def _extract_extension(self, file_path: Path) -> str:
        """Processes multi-part extensions (e.g. .tar.gz) and strips trailing dots/spaces."""
        filename = file_path.name.strip().rstrip('.')
        
        suffixes = [s.lower() for s in Path(filename).suffixes]
        if len(suffixes) >= 2:
            compound_ext = "".join(suffixes[-2:])
            if compound_ext in self.ext_to_category:
                return compound_ext
        
        if suffixes:
            return suffixes[-1]
            
        return ""

    def get_category(self, file_path: Path) -> str:
        """Determines category based on normalized extension or MIME type."""
        ext = self._extract_extension(file_path)
        if ext in self.ext_to_category:
            return self.ext_to_category[ext]
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            main_type = mime_type.split("/")[0].capitalize()
            if main_type in ["Image", "Audio", "Video", "Text"]:
                return main_type
            
        return "Others"

    def get_size_bucket(self, file_path: Path) -> str:
        """Classifies the file into a predefined size bucket based on byte size."""
        try:
            file_size = file_path.stat().st_size
        except OSError:
            return "Unknown Size"

        for bucket_name, (min_size, max_size) in self.SIZE_BUCKETS.items():
            if min_size <= file_size < max_size:
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
        Executes file organization with optional deduplication, date hierarchy, and size-bucket classification.
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
                if file_path.parent.name in self.rules.keys() or file_path.parent.name == "Others":
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
                dest_file_path = dest_dir / file_path.name

                counter = 1
                orig_stem = file_path.stem
                ext = self._extract_extension(file_path)
                while dest_file_path.exists():
                    dest_file_path = dest_dir / f"{orig_stem}_{counter}{ext}"
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