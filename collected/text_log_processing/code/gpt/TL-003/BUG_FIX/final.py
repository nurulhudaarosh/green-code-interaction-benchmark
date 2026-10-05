def dedup_lines(in_path, out_path, mode='exact'):
    if mode not in ('exact', 'normalized'):
        raise ValueError("mode must be 'exact' or 'normalized'")

    seen = set()
    total = 0
    unique = 0

    with open(in_path, 'r', encoding='utf-8', newline='') as infile, \
         open(out_path, 'w', encoding='utf-8', newline='') as outfile:

        for line in infile:
            total += 1

            # Remove only the line terminator.
            # This also correctly handles a final line with no newline.
            content = line[:-2] if line.endswith('\r\n') else \
                      line[:-1] if line.endswith(('\n', '\r')) else line

            if mode == 'normalized':
                # Collapse all whitespace and lowercase.
                key = ' '.join(content.split()).lower()
            else:
                key = content

            if key in seen:
                continue

            seen.add(key)
            outfile.write(line)
            unique += 1

    return {
        'total': total,
        'unique': unique,
        'removed': total - unique
    }