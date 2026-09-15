#!/usr/bin/env python3
"""Repair a dataset.json whose generator wrote Python-ish syntax inside JSON
strings: unescaped quotes (``"GET /x"`` inside log lines), invalid escapes
(``\\d``, ``\\s``), single-quoted Python strings, ``[x] * 1000`` repetition
and True/False/None literals.

Needed when a member's Drive dataset.json is corrupt at the SOURCE (so
re-downloading cannot fix it). The repaired copy becomes the frozen local
dataset.

Approach: a backtracking recursive-descent parser (continuation passing).
Inside a string, a ``"`` whose follower looks structural (``:,}]`` or EOF)
is ambiguous - real close vs embedded quote. The parser first tries
"close" and lets the REST of the document decide; on failure it
backtracks and treats the quote as embedded. ``--check`` only validates.

Usage:
    python3 scripts/repair_dataset.py IN.json -o OUT.json
    python3 scripts/repair_dataset.py IN.json --check
"""

import argparse
import json
import re
import sys

sys.setrecursionlimit(200_000)

STRUCTURAL = ":,}]"
PY_REPEAT = re.compile(r"\*\s*\d+")
NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
CTRL = re.compile(r"[\x00-\x1f]")


class Fail(Exception):
    pass


def skip_ws(t, i):
    n = len(t)
    while i < n and t[i] in " \t\r\n":
        i += 1
    return i


class Parser:
    def __init__(self, t, budget=5_000_000):
        self.t = t
        self.n = len(t)
        self.steps = 0
        self.budget = budget
        self.notes = {"embedded_quotes": 0, "invalid_escapes": 0,
                      "py_strings": 0, "py_repeat": 0, "py_bool": 0}

    def tick(self):
        self.steps += 1
        if self.steps > self.budget:
            raise Fail("step budget exceeded")

    def parse(self):
        t, n = self.t, self.n

        def top(v, j):
            j = skip_ws(t, j)
            if j != n:
                raise Fail(f"trailing garbage at {j}: {t[j:j + 50]!r}")
            return v

        i = skip_ws(t, 0)
        return self.value(i, top)

    # -------------------------------------------------------------- values
    def value(self, i, k):
        self.tick()
        t, n = self.t, self.n
        if i >= n:
            raise Fail("EOF")
        c = t[i]
        if c == '"':
            return self.string(i, k)
        if c == "[":
            return self.array(i, k)
        if c == "{":
            return self.obj(i, k)
        if c == "'":
            return self.py_string(i, k)
        for lit, val in (("true", True), ("false", False), ("null", None),
                         ("True", True), ("False", False), ("None", None)):
            if t.startswith(lit, i):
                if lit[0].isupper():
                    self.notes["py_bool"] += 1
                return k(val, i + len(lit))
        m = NUMBER.match(t, i)
        if m:
            s = m.group(0)
            return k(json.loads(s), m.end())
        raise Fail(f"unexpected {c!r} at {i}: {t[i:i + 40]!r}")

    # -------------------------------------------------- JSON string + backtrack
    def string(self, i, k):
        """Parse a JSON string starting at t[i]=='"'.

        Ambiguous quotes (followed by a structural char) are first tried as
        the string END; if the rest of the document fails to parse, the
        quote is kept as an embedded python/code quote instead.
        Produces tokens; _assemble() then decodes escapes with awareness
        of python string-literal context (a \\n between statements is a
        real newline; a \\n inside a python string literal must stay as
        backslash-n source text).
        """
        t, n = self.t, self.n
        tokens = []
        pos = i + 1
        while True:
            self.tick()
            if pos >= n:
                raise Fail("unterminated string")
            c = t[pos]
            if c == "\\":
                nxt = t[pos + 1] if pos + 1 < n else ""
                if nxt == "u" and re.match(r"u[0-9a-fA-F]{4}", t[pos + 1:pos + 6]):
                    tokens.append(("u", t[pos + 2:pos + 6]))
                    pos += 6
                elif nxt and nxt not in '"\\/bfnrtu':
                    self.notes["invalid_escapes"] += 1
                    tokens.append(("inv", nxt))
                    pos += 2
                elif nxt:
                    tokens.append(("esc", nxt))
                    pos += 2
                else:
                    raise Fail("dangling backslash")
                continue
            if c == '"':
                j = skip_ws(t, pos + 1)
                follower = t[j] if j < n else ""
                if follower == "" or follower in STRUCTURAL:
                    try:
                        return k(self._assemble(tokens), pos + 1)
                    except Fail:
                        pass  # backtrack: treat this quote as embedded
                self.notes["embedded_quotes"] += 1
                tokens.append(("dq",))
                pos += 1
                continue
            if c == "'":
                tokens.append(("sq",))
                pos += 1
                continue
            tokens.append(("ch", c))
            pos += 1

    # ------------------------------- python-context-aware escape decoding
    _ESC_MAP = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f',
                '"': '"', '\\': '\\', '/': '/'}

    @classmethod
    def _assemble(cls, tokens):
        out = []
        n = len(tokens)
        i = 0
        # state: n normal, s single, d double, S triple-single, D triple-double, c comment
        state = "n"
        while i < n:
            kind = tokens[i][0]
            if kind == "u":
                out.append(chr(int(tokens[i][1], 16)))
                i += 1
            elif kind == "inv":
                out.append("\\" + tokens[i][1])
                i += 1
            elif kind == "ch":
                c = tokens[i][1]
                if state == "c" and c == "\n":
                    state = "n"
                elif state == "n" and c == "#":
                    state = "c"
                out.append(c)
                i += 1
            elif kind == "sq":
                triple = i + 2 < n and tokens[i + 1][0] == "sq" and tokens[i + 2][0] == "sq"
                if state == "n" and triple:
                    state = "S"
                    out.append("'''")
                    i += 3
                elif state == "n":
                    state = "s"
                    out.append("'")
                    i += 1
                elif state == "s":
                    state = "n"
                    out.append("'")
                    i += 1
                elif state == "S" and triple:
                    state = "n"
                    out.append("'''")
                    i += 3
                else:  # content inside d/D/c/s/S stays
                    out.append("'")
                    i += 1
            elif kind == "dq":
                triple = i + 2 < n and tokens[i + 1][0] == "dq" and tokens[i + 2][0] == "dq"
                if state == "n" and triple:
                    state = "D"
                    out.append('"""')
                    i += 3
                elif state == "n":
                    state = "d"
                    out.append('"')
                    i += 1
                elif state == "d":
                    state = "n"
                    out.append('"')
                    i += 1
                elif state == "D" and triple:
                    state = "n"
                    out.append('"""')
                    i += 3
                else:
                    out.append('"')
                    i += 1
            else:  # esc
                c = tokens[i][1]
                if state in ("n", "c"):
                    if c == "n" and state == "c":
                        state = "n"
                    out.append(cls._ESC_MAP[c])
                else:
                    # inside a python string literal: keep source text
                    out.append("\\" + c if c != "\\" else "\\\\")
                i += 1
        return "".join(out)

    # -------------------------------------------------- python '...' string
    def py_string(self, i, k):
        self.notes["py_strings"] += 1
        t, n = self.t, self.n
        pos = i + 1
        buf = []
        while pos < n:
            c = t[pos]
            if c == "\\" and pos + 1 < n:
                nxt = t[pos + 1]
                buf.append({"n": "\n", "t": "\t", "r": "\r", "'": "'"}.get(nxt, "\\" + nxt))
                pos += 2
                continue
            if c == "'":
                return k("".join(buf), pos + 1)
            buf.append(c)
            pos += 1
        raise Fail("unterminated python string")

    # -------------------------------------------------------------- array
    def array(self, i, k):
        t = self.t

        def elements(j, acc):
            self.tick()
            j = skip_ws(t, j)
            if j < self.n and t[j] == "]":
                return k(acc, j + 1)

            def elem_cont(v, m):
                m = skip_ws(t, m)
                mm = PY_REPEAT.match(t, m)
                if mm:
                    self.notes["py_repeat"] += 1
                    m = skip_ws(t, mm.end())
                if m < self.n and t[m] == ",":
                    m2 = skip_ws(t, m + 1)
                    if m2 < self.n and t[m2] == "]":  # trailing comma
                        return k(acc + [v], m2 + 1)
                    return elements(m2, acc + [v])
                if m < self.n and t[m] == "]":
                    return k(acc + [v], m + 1)
                raise Fail(f"expected , or ] at {m}: {t[m:m + 30]!r}")

            return self.value(j, elem_cont)

        return elements(i + 1, [])

    # -------------------------------------------------------------- object
    def obj(self, i, k):
        t = self.t

        def members(j, acc):
            self.tick()
            j = skip_ws(t, j)
            if j < self.n and t[j] == "}":
                return k(acc, j + 1)

            def key_cont(key, m):
                m = skip_ws(t, m)
                if m >= self.n or t[m] != ":":
                    raise Fail(f"expected : at {m}")
                p = skip_ws(t, m + 1)

                def val_cont(v, q):
                    q = skip_ws(t, q)
                    if q < self.n and t[q] == ",":
                        q2 = skip_ws(t, q + 1)
                        if q2 < self.n and t[q2] == "}":  # trailing comma
                            return k({**acc, key: v}, q2 + 1)
                        return members(q2, {**acc, key: v})
                    if q < self.n and t[q] == "}":
                        return k({**acc, key: v}, q + 1)
                    raise Fail(f"expected , or }} at {q}: {t[q:q + 30]!r}")

                return self.value(p, val_cont)

            if j >= self.n or t[j] != '"':
                raise Fail(f"expected key string at {j}")
            return self.string(j, key_cont)

        return members(i + 1, {})


def neuter_tests(text):
    """Replace per-task "tests": {...} blocks with an empty stub.

    public_tests are not used by the measurement pipeline (harnesses derive
    from reference signatures), and they hold unrepairable Python
    expressions (f-strings, comprehensions). Line-based: works on the
    pretty-printed layout this generator produces.
    """
    lines = text.splitlines(keepends=True)
    out, i, count = [], 0, 0
    while i < len(lines):
        if lines[i].strip() == '"tests": {':
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith('"reference_solution"'):
                j += 1
            out.append('"tests": {\n"public_tests": []\n},\n')
            i = j
            count += 1
        else:
            out.append(lines[i])
            i += 1
    return "".join(out), count


def validate(data):
    tasks = data.get("tasks", []) if isinstance(data, dict) else data
    if not tasks:
        return False, "no tasks"
    ids = [str(t.get("task_id")) for t in tasks]
    if len(set(ids)) != len(ids):
        return False, "duplicate task ids"
    bad = []
    for t in tasks:
        code = (t.get("reference_solution") or {}).get("code", "")
        try:
            compile(code, str(t.get("task_id", "?")), "exec")
        except SyntaxError as e:
            bad.append(f"{t.get('task_id')}: {e}")
    if bad:
        return False, "reference solutions do not compile:\n  " + "\n  ".join(bad)
    return True, f"{len(tasks)} tasks ok ({ids[0]}..{ids[-1]})"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("infile")
    ap.add_argument("-o", "--output")
    ap.add_argument("--check", action="store_true", help="only validate, write nothing")
    ap.add_argument("--keep-tests", action="store_true",
                    help="do not neuter public_tests blocks before repairing")
    args = ap.parse_args()

    raw = open(args.infile, encoding="utf-8").read()
    text = raw
    neutered = 0
    if not args.keep_tests:
        text, neutered = neuter_tests(raw)
    p = Parser(text)
    try:
        data = p.parse()
    except Fail as e:
        print(f"REPAIR FAILED: {e}")
        print(f"notes: {p.notes}")
        return 1
    print(f"repair ok (tests blocks stubbed: {neutered})")
    print(f"fixes: {p.notes}")
    ok, msg = validate(data)
    print(f"validate: {'OK' if ok else 'FAILED'} - {msg}")
    if args.check:
        return 0 if ok else 1
    if not args.output:
        print("no -o given; not writing")
        return 0 if ok else 1
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"wrote {args.output}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
