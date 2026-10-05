def dedup_lines(in_path, out_path, mode='exact'):
    """
    Remove duplicate lines from a file, keeping first occurrences in order.

    Args:
        in_path:  Path to the input file.
        out_path: Path to the output file.
        mode:     'exact' (default) compares raw lines without trailing newline;
                  'normalized' compares ' '.join(line.strip().lower().split()).

    Returns:
        dict with keys 'total', 'unique', 'removed'.
    """
    if mode not in ('exact', 'normalized'):
        raise ValueError("mode must be 'exact' or 'normalized'")

    seen = set()
    total = 0
    unique = 0

    with open(in_path, 'r', encoding='utf-8', newline='') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='') as fout:

        for raw in fin:
            total += 1

            # Strip only the trailing newline (and any \r before it) for 'exact'
            # so we don't accidentally mutate meaningful whitespace.
            line = raw
            if line.endswith('\n'):
                line = line[:-1]
                if line.endswith('\r'):
                    line = line[:-1]

            if mode == 'normalized':
                key = ' '.join(line.strip().lower().split())
            else:
                key = line

            if key in seen:
                continue

            seen.add(key)
            unique += 1
            fout.write(line + '\n')

    return {
        'total': total,
        'unique': unique,
        'removed': total - unique,
    }