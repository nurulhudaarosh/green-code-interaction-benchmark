def dedup_lines(in_path, out_path, mode='exact'):
    if mode not in ('exact', 'normalized'):
        raise ValueError("mode must be 'exact' or 'normalized'")

    seen = set()
    total = unique = 0

    with open(in_path, 'r', encoding='utf-8', newline='') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='') as fout:
        for raw in fin:
            total += 1
            line = raw.rstrip('\r\n')
            key = ' '.join(line.strip().lower().split()) if mode == 'normalized' else line
            if key in seen:
                continue
            seen.add(key)
            unique += 1
            fout.write(line + '\n')

    return {'total': total, 'unique': unique, 'removed': total - unique}