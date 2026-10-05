import re


def analyze_error_log(path, top_n=10):
    """
    Read a UTF-8 server log file line by line, extract ERROR lines,
    normalize messages (mask IPs and numbers, collapse whitespace),
    and return signature counts plus the top-N signatures.

    Line format: '[timestamp] LEVEL message'

    Returns:
        {
            'counts': {signature: count, ...},
            'malformed': int,          # blank / unparseable lines
            'top': [[signature, count], ...]  # count desc, then sig asc
        }
    """
    # A well-formed line: [timestamp] LEVEL message
    line_re = re.compile(r'^\[[^\]]*\]\s+([A-Z]+)\s+(.*)$')
    # IPv4 address
    ip_re = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    # Any run of digits, optionally with a decimal part
    num_re = re.compile(r'\d+(?:\.\d+)?')
    # Runs of whitespace
    ws_re = re.compile(r'\s+')

    counts = {}
    malformed = 0

    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\r\n')

            if not line.strip():
                malformed += 1
                continue

            m = line_re.match(line)
            if not m:
                malformed += 1
                continue

            level, msg = m.group(1), m.group(2)
            if level != 'ERROR':
                continue

            # Mask IPs first so dotted quads don't get split into <N>.<N>...
            msg = ip_re.sub('<IP>', msg)
            msg = num_re.sub('<N>', msg)
            msg = ws_re.sub(' ', msg).strip()

            if not msg:
                malformed += 1
                continue

            counts[msg] = counts.get(msg, 0) + 1

    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    return {
        'counts': counts,
        'malformed': malformed,
        'top': [[sig, cnt] for sig, cnt in top],
    }