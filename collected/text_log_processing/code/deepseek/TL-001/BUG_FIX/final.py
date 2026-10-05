import re


def analyze_error_log(path, top_n=10):
    line_re = re.compile(r'^\[[^\]]*\]\s+([A-Za-z]+)\s+(.*)$')
    ip_re   = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    num_re  = re.compile(r'\d+(?:\.\d+)?')
    ws_re   = re.compile(r'\s+')

    counts = {}
    malformed = 0

    # errors='replace' so a stray non-UTF-8 byte becomes U+FFFD instead of raising
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
            try:
                line = raw.rstrip('\r\n')

                if not line.strip():
                    malformed += 1
                    continue

                m = line_re.match(line)
                if not m:
                    malformed += 1
                    continue

                level, msg = m.group(1), m.group(2)
                if level.upper() != 'ERROR':
                    continue

                msg = ip_re.sub('<IP>', msg)
                msg = num_re.sub('<N>', msg)
                msg = ws_re.sub(' ', msg).strip()

                if not msg:
                    malformed += 1
                    continue

                counts[msg] = counts.get(msg, 0) + 1

            except Exception:
                # Belt-and-suspenders: never let one bad line abort the scan.
                malformed += 1
                continue

    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return {
        'counts': counts,
        'malformed': malformed,
        'top': [[sig, cnt] for sig, cnt in top],
    }