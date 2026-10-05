import sys
from collections import Counter

def deduplicate_with_counts(input_stream, output_stream):
    """
    Counts exact duplicate lines (preserving all spaces, tabs, and indentation)
    while normalizing standard line terminators (\\r\\n, \\r, \\n, or EOF without newline).
    """
    counts = Counter()

    for line in input_stream:
        # Strip ONLY the line terminator characters from the end,
        # preserving all intentional trailing spaces, tabs, and content.
        if line.endswith('\r\n'):
            line_body = line[:-2]
        elif line.endswith(('\n', '\r')):
            line_body = line[:-1]
        else:
            # Handles final line at EOF without a trailing newline
            line_body = line

        counts[line_body] += 1

    for line_body, count in counts.items():
        output_stream.write(f"{count:>7} {line_body}\n")

if __name__ == "__main__":
    deduplicate_with_counts(sys.stdin, sys.stdout)