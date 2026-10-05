def dedup_lines(in_path, out_path, mode='exact'):
    if mode not in ('exact', 'normalized'):
        raise ValueError("mode must be 'exact' or 'normalized'")

    total = unique = removed = 0
    seen = set()

    with open(in_path, 'r', encoding='utf-8', newline='') as infile, \
         open(out_path, 'w', encoding='utf-8', newline='') as outfile:

        for line in infile:
            total += 1

            if mode == 'exact':
                key = line
            else:
                key = ' '.join(line.strip().lower().split())

            if key in seen:
                removed += 1
            else:
                seen.add(key)
                outfile.write(line)
                unique += 1

    return {
        'total': total,
        'unique': unique,
        'removed': removed
    }