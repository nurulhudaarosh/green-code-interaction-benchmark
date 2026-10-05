import sys
from collections import Counter

def deduplicate_with_counts(input_stream, output_stream):
    """
    Reads lines from input_stream, counts duplicates, and writes
    each unique line prefixed by its occurrence count in first-seen order.
    """
    counts = Counter()

    for line in input_stream:
        # Strip trailing newlines/carriage returns to cleanly handle blank lines
        clean_line = line.rstrip('\r\n')
        counts[clean_line] += 1

    for line, count in counts.items():
        output_stream.write(f"{count:>7} {line}\n")

if __name__ == "__main__":
    # Reads from standard input (pipe/redirect) and writes to standard output
    deduplicate_with_counts(sys.stdin, sys.stdout)