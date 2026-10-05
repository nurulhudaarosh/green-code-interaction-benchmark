def dedup_lines(in_path, out_path, mode='exact'):
    if mode not in ('exact', 'normalized'):
        raise ValueError("mode must be 'exact' or 'normalized'")

    seen = set()
    total = unique = 0
    last_kept_had_nl = False

    with open(in_path, 'r', encoding='utf-8') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='\n') as fout:
        for raw in fin:
            total += 1
            had_nl = raw.endswith('\n')
            line = raw[:-1] if had_nl else raw
            key = ' '.join(line.split()).lower() if mode == 'normalized' else line
            if key in seen:
                continue
            seen.add(key)
            if unique:
                fout.write('\n')  # terminator for the previous kept line
            fout.write(line)
            unique += 1
            last_kept_had_nl = had_nl
        if unique and last_kept_had_nl:
            fout.write('\n')

    return {'total': total, 'unique': unique, 'removed': total - unique}