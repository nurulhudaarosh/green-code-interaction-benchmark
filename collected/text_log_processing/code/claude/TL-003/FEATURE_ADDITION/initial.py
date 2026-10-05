def dedupe_lines(text):
    seen = set()
    unique = []
    lines = text.splitlines()
    for line in lines:
        if line not in seen:
            seen.add(line)
            unique.append(line)
    return "\n".join(unique), len(lines), len(unique), len(lines) - len(unique)


text = "a\nb\na\nc\nb"
result, total, unique, removed = dedupe_lines(text)
print(result)
print(total, unique, removed)  # 5 3 2