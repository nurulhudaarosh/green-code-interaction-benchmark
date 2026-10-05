import argparse
import re
import unicodedata
from pathlib import Path

# Common typographic / smart quote and punctuation replacements
PUNCTUATION_MAP = {
    "\u2018": "'",  # Left single quotation mark
    "\u2019": "'",  # Right single quotation mark
    "\u201a": "'",  # Single low-9 quotation mark
    "\u201b": "'",  # Single high-reversed-9 quotation mark
    "\u201c": '"',  # Left double quotation mark
    "\u201d": '"',Here is a Python script that normalizes text files by addressing Unicode inconsistencies, non-standard whitespace, zero-width characters, typographic punctuation, and blank line sprawl.

### `normalize_text.py`