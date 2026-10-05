def dedupe_lines(text, mode="exact"):
    if mode == "exact":
        key = lambda s: s
    elif mode == "normalized":
        key = lambda s: " ".join(s.lower().split())
    else:
        raise ValueError("mode must be 'exact' or 'normalized'")

    seen = set()
    unique = []
    lines = text.splitlines()
    for line in lines:
        k = key(line)
        if k not in seen:
            seen.add(k)
            unique.append(line)  # original line is written, not the key
    return "\n".join(unique), len(lines), len(unique), len(lines) - len(unique)


text = "Hello  World\nhello world\n  HELLO WORLD \nbye"
print(dedupe_lines(text, "exact")[1:])       # (4, 4, 0)
print(dedupe_lines(text, "normalized"))      # ('Hello  World\nbye', 4, 2, 2)