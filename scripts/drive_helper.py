#!/usr/bin/env python3
"""One gdown operation per process, so the pipeline can enforce a hard
wall-clock timeout (gdown's internal retries can otherwise hang forever).

Usage:
    drive_helper.py list <url> <output_dir>
        -> prints {"ok": true, "files": [{"id":..., "path":...}]}
    drive_helper.py get <file_id> <output_dir>
        -> prints {"ok": true, "path": ...} or {"ok": false, "error": ...}
"""

import json
import socket
import sys
from pathlib import Path

socket.setdefaulttimeout(30)


def main():
    if len(sys.argv) != 4:
        print(json.dumps({"ok": False, "error": "usage: list|get a b"}))
        return 2
    mode, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    import gdown  # noqa: PLC0415 - isolated on purpose

    if mode == "list":
        try:
            files = gdown.download_folder(
                url=a, output=b, quiet=True, skip_download=True,
                resume=True, use_cookies=False)
            out = [{"id": f.id, "path": str(Path(f.local_path))}
                   for f in files or []]
            print(json.dumps({"ok": True, "files": out}))
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"ok": False, "error": str(e)[:300]}))
        return 0

    if mode == "get":
        try:
            out = gdown.download(id=a, output=b, quiet=True, resume=True)
            print(json.dumps({"ok": True, "path": str(out) if out else None}))
        except Exception as e:  # noqa: BLE001
            print(json.dumps({"ok": False, "error": str(e)[:300]}))
        return 0

    print(json.dumps({"ok": False, "error": f"unknown mode {mode}"}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
