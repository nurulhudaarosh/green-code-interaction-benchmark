import argparse
import sys
from collections import Counter


def strip_line_terminator(line: str) -> str:
    """Removes standard line endings (\r\n, \n, \r) without stripping content whitespace."""
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\n", "\r")):
        return line[:-1]
    return line


def normalize_text(text: str) -> str:
    """Collapses consecutive whitespace runs into a single space and lowers case."""
    return " ".join(text.split()).casefold()


def deduplicate_with_counts(input_stream, output_stream, normalize: bool = False):
    """Counts duplicate lines in first-seen order, fixing missing newlines and whitespace bugs.

    Correctly handles:
      - Empty input stream (zero bytes -> exits cleanly without output).
      - Pure empty lines (counts empty lines as distinct keys without crashing).
      - All-duplicate lines (emits exactly 1 row with full occurrence count).
      - Missing EOF newlines & mixed CRLF/LF line endings.
      - Case/whitespace normalized grouping with raw first-occurrence display.
    """
    counts = Counter()
    first_seen = {}

    for raw_line in input_stream:
        line_body = strip_line_terminator(raw_line)

        # Normalize or use raw line body
        key = normalize_text(line_body) if normalize else line_body

        if key not in first_seen:
            first_seen[key] = line_body

        counts[key] += 1

    # Empty input stream: loop evaluates to 0 iterations, nothing is emitted
    # All-duplicate input: counts has length 1, exactly 1 line is emitted
    for key, count in counts.items():
        output_stream.write(f"{count:>7} {first_seen[key]}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Deduplicate lines with counts preserving first-seen order."
    )
    parser.add_argument(
        "-n",
        "--normalize",
        action="store_true",
        help="Normalize case and collapse internal/outer whitespace when comparing.",
    )
    args = parser.parse_args()

    deduplicate_with_counts(sys.stdin, sys.stdout, normalize=args.normalize)


if __name__ == "__main__":
    main()