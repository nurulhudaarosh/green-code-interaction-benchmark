from __future__ import annotations
import json
import math
import operator
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

# ───────────── Path resolution ─────────────

class _Missing:
    def __repr__(self): return "<MISSING>"
MISSING = _Missing()


@dataclass(frozen=True)
class Hit:
    path: str
    value: Any = MISSING
    blocked_by: str | None = None
    blocked_type: str | None = None

    @property
    def present(self) -> bool:
        return self.value is not MISSING and self.blocked_by is None

    @property
    def blocked(self) -> bool:
        return self.blocked_by is not None


def split_path(path: str) -> list[tuple[str, bool]]:
    """'a.b\\.c.*' -> [('a',F),('b.c',F),('*',T)]. Escapes: \\. \\* \\\\"""
    segs, cur, escaped, i = [], [], False, 0
    while i < len(path):
        ch = path[i]
        if ch == "\\" and i + 1 < len(path) and path[i + 1] in ".*\\":
            cur.append(path[i + 1]); escaped = True; i += 2; continue
        if ch == ".":
            s = "".join(cur); segs.append((s, s == "*" and not escaped))
            cur, escaped = [], False
        else:
            cur.append(ch)
        i += 1
    s = "".join(cur)
    segs.append((s, s == "*" and not escaped))
    return segs


def _join(prefix: str, key: Any) -> str:
    k = str(key).replace("\\", "\\\\").replace(".", "\\.")
    return f"{prefix}.{k}" if prefix else k


def resolve(cfg: Any, path: str) -> list[Hit]:
    """Non-wildcard paths yield exactly one Hit (present, missing, or blocked)."""
    hits = [Hit("", cfg)]
    for seg, wild in split_path(path):
        nxt: list[Hit] = []
        for h in hits:
            if h.blocked:
                nxt.append(h); continue
            if not h.present:
                nxt.append(Hit(_join(h.path, seg))); continue
            node = h.value
            if wild:
                if isinstance(node, dict):
                    nxt += [Hit(_join(h.path, k), v) for k, v in node.items()]
                elif isinstance(node, (list, tuple)):
                    nxt += [Hit(_join(h.path, i), v) for i, v in enumerate(node)]
                else:
                    nxt.append(Hit(_join(h.path, "*"), MISSING, h.path or "<root>", type(node).__name__))
            elif isinstance(node, dict):
                p = _join(h.path, seg)
                nxt.append(Hit(p, node[seg]) if seg in node else Hit(p))
            elif isinstance(node, (list, tuple)):
                p = _join(h.path, seg)
                try:
                    idx = int(seg)
                except ValueError:
                    nxt.append(Hit(p, MISSING, h.path or "<root>", "list")); continue
                nxt.append(Hit(p, node[idx]) if -len(node) <= idx < len(node) else Hit(p))
            else:
                nxt.append(Hit(_join(h.path, seg), MISSING, h.path or "<root>", type(node).__name__))
        hits = nxt
    return hits


def values(cfg: Any, path: str) -> list[Hit]:
    return [h for h in resolve(cfg, path) if h.present]


def get_path(cfg: Any, path: str, default: Any = None) -> Any:
    vs = values(cfg, path)
    return vs[0].value if vs else default


def exists(cfg: Any, path: str) -> bool:
    return bool(values(cfg, path))


# ───────────── Type / bool helpers ─────────────

TYPES: dict[str, type] = {"int": int, "float": float, "str": str, "bool": bool,
                          "list": list, "dict": dict, "null": type(None)}
_TRUE, _FALSE = {"true", "yes", "on", "1"}, {"false", "no", "off", "0"}


def type_matches(v: Any, types: Iterable[type]) -> bool:
    for t in types:
        if t is bool:
            if isinstance(v, bool): return True
        elif t is int:
            if isinstance(v, int) and not isinstance(v, bool): return True
        elif t is float:
            if isinstance(v, (int, float)) and not isinstance(v, bool): return True
        elif isinstance(v, t):
            return True
    return False


def as_bool(v: Any, coerce: bool = False) -> bool | None:
    if isinstance(v, bool): return v
    if coerce and isinstance(v, str):
        s = v.strip().lower()
        if s in _TRUE: return True
        if s in _FALSE: return False
    return None


def strict_eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def is_num(v: Any) -> bool:
    return type_matches(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))


_CMP = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge}


def safe_cmp(op: str, a: Any, b: Any) -> bool:
    """Bool-strict; ordering only for number/number or str/str."""
    if op == "==": return strict_eq(a, b)
    if op == "!=": return not strict_eq(a, b)
    if is_num(a) and is_num(b): return _CMP[op](a, b)
    if isinstance(a, str) and isinstance(b, str): return _CMP[op](a, b)
    return False


# ───────────── Single-field checks ─────────────

Rule = Callable[[Any], list[str]]


def _blocked(h: Hit) -> str:
    return f"'{h.path}' is unreachable: '{h.blocked_by}' is {h.blocked_type}, not an object/list"


def check_field(c: Any, spec: dict) -> list[str]:
    errs: list[str] = []
    raw = spec.get("type", [])
    types = [TYPES[t] for t in ([raw] if isinstance(raw, str) else raw)]
    for h in resolve(c, spec["path"]):
        if h.blocked:
            errs.append(_blocked(h)); continue
        if not h.present:
            if spec.get("required"): errs.append(f"'{h.path}' is required")
            continue
        v, p = h.value, h.path
        if types:
            ok = type_matches(v, types)
            if not ok and spec.get("coerce_bool") and bool in types:
                ok = as_bool(v, coerce=True) is not None
            if not ok:
                errs.append(f"'{p}' must be {' or '.join(t.__name__ for t in types)}, got {type(v).__name__}")
                continue
        if "min" in spec or "max" in spec:
            if not is_num(v):
                errs.append(f"'{p}' must be a number for range check, got {type(v).__name__}"
                            + (" (bool is not a number)" if isinstance(v, bool) else ""))
                continue
            if "min" in spec and v < spec["min"]: errs.append(f"'{p}' must be >= {spec['min']}, got {v}")
            if "max" in spec and v > spec["max"]: errs.append(f"'{p}' must be <= {spec['max']}, got {v}")
        if ("min_len" in spec or "max_len" in spec) and hasattr(v, "__len__"):
            n = len(v)
            if n < spec.get("min_len", 0): errs.append(f"'{p}' length must be >= {spec['min_len']}, got {n}")
            if "max_len" in spec and n > spec["max_len"]:
                errs.append(f"'{p}' length must be <= {spec['max_len']}, got {n}")
        if "enum" in spec and not any(strict_eq(v, a) for a in spec["enum"]):
            errs.append(f"'{p}' must be one of {spec['enum']!r}, got {v!r}")
        if "pattern" in spec and not (isinstance(v, str) and re.fullmatch(spec["pattern"], v)):
            errs.append(f"'{p}' must match {spec.get('pattern_desc', spec['pattern'])}, got {v!r}")
    return errs


# ───────────── Conditions ─────────────

_COND_OPS = {"eq": "==", "ne": "!=", "gt": ">", "ge": ">=", "lt": "<", "le": "<="}


def eval_cond(c: Any, cond: dict) -> bool:
    if "all" in cond: return all(eval_cond(c, x) for x in cond["all"])
    if "any" in cond: return any(eval_cond(c, x) for x in cond["any"])
    if "not" in cond: return not eval_cond(c, cond["not"])
    present = [h.value for h in values(c, cond["path"])]
    if "exists" in cond: return bool(present) == cond["exists"]

    def one(v: Any) -> bool:
        for k, op in _COND_OPS.items():
            if k in cond and not safe_cmp(op, v, cond[k]): return False
        if "in" in cond and not any(strict_eq(v, a) for a in cond["in"]): return False
        if "truthy" in cond and bool(v) != cond["truthy"]: return False
        return True

    return any(one(v) for v in present)   # missing path => False


def describe(cond: dict) -> str:
    return json.dumps(cond, sort_keys=True, default=str)


# ───────────── Cross-field rules ─────────────

def _msg(s: dict, default: str) -> str:
    return s.get("message", default)


def _found(c: Any, paths: list[str]) -> list[str]:
    return [p for p in paths if exists(c, p)]


def x_requires_if(c, s):
    if not eval_cond(c, s["if"]): return []
    return [_msg(s, f"'{p}' is required when {describe(s['if'])}")
            for p in s["then_require"] if not exists(c, p)]


def x_forbids_if(c, s):
    if not eval_cond(c, s["if"]): return []
    return [_msg(s, f"'{p}' must not be set when {describe(s['if'])}")
            for p in s["then_forbid"] if exists(c, p)]


def x_if_then(c, s):
    if eval_cond(c, s["if"]) and not eval_cond(c, s["then"]):
        return [_msg(s, f"when {describe(s['if'])}, expected {describe(s['then'])}")]
    return []


def x_all_or_none(c, s):
    f = _found(c, s["paths"])
    if 0 < len(f) < len(s["paths"]):
        return [_msg(s, f"{s['paths']} must be set together; missing {[p for p in s['paths'] if p not in f]}")]
    return []


def x_at_least_one(c, s):
    return [] if _found(c, s["paths"]) else [_msg(s, f"At least one of {s['paths']} must be set")]


def x_exactly_one(c, s):
    f = _found(c, s["paths"])
    return [] if len(f) == 1 else [_msg(s, f"Exactly one of {s['paths']} must be set, found {f}")]


def x_mutually_exclusive(c, s):
    f = _found(c, s["paths"])
    return [_msg(s, f"Only one of {s['paths']} may be set, found {f}")] if len(f) > 1 else []


def x_compare(c, s):
    lefts = values(c, s["left"])
    if "right_value" in s:
        pairs = [(h.path, h.value, repr(s["right_value"]), s["right_value"]) for h in lefts]
    else:
        rights = values(c, s["right"])
        if len(rights) == 1: rights = rights * len(lefts)
        elif len(rights) != len(lefts): return []
        pairs = [(l.path, l.value, f"'{r.path}' ({r.value!r})", r.value) for l, r in zip(lefts, rights)]
    return [_msg(s, f"'{lp}' ({lv!r}) must be {s['op']} {rd}")
            for lp, lv, rd, rv in pairs if not safe_cmp(s["op"], lv, rv)]


def x_unique(c, s):
    seen: dict[str, str] = {}
    errs = []
    for h in values(c, s["path"]):
        key = json.dumps([type(h.value).__name__, h.value], sort_keys=True, default=str)
        if key in seen: errs.append(_msg(s, f"'{h.path}' duplicates '{seen[key]}' (value {h.value!r})"))
        else: seen[key] = h.path
    return errs


def x_sum(c, s):
    hs = values(c, s["path"])
    bad = [h for h in hs if not is_num(h.value)]
    if bad:
        return [f"'{h.path}' must be a number to be summed, got {type(h.value).__name__}" for h in bad]
    total = sum(h.value for h in hs)
    if "right_value" in s: target, d = s["right_value"], repr(s["right_value"])
    else:
        r = values(c, s["right"])
        if not r: return []
        target, d = r[0].value, f"'{r[0].path}' ({r[0].value!r})"
    return [] if safe_cmp(s["op"], total, target) else \
        [_msg(s, f"sum of '{s['path']}' ({total}) must be {s['op']} {d}")]


def x_count(c, s):
    n = len(values(c, s["path"]))
    errs = []
    if "min" in s and n < s["min"]: errs.append(_msg(s, f"'{s['path']}' needs >= {s['min']} item(s), found {n}"))
    if "max" in s and n > s["max"]: errs.append(_msg(s, f"'{s['path']}' allows <= {s['max']} item(s), found {n}"))
    return errs


def x_map(c, s):
    """If `path` == key, then `then_path` must be one of table[key]."""
    errs = []
    for src in values(c, s["path"]):
        for key, allowed in s["table"].items():
            if strict_eq(src.value, key):
                for dst in values(c, s["then_path"]):
                    if not any(strict_eq(dst.value, a) for a in allowed):
                        errs.append(_msg(s, f"'{dst.path}' must be one of {allowed!r} when "
                                            f"'{src.path}' is {key!r}, got {dst.value!r}"))
    return errs


def x_depends(c, s, graph: dict[str, list[str]]):
    """Walk dependency chains from `path`; report the first missing link with its chain."""
    errs, seen_missing = [], set()

    def walk(node: str, chain: list[str], visiting: frozenset):
        for dep in graph.get(node, []):
            if dep in visiting: continue
            if not exists(c, dep):
                if (chain[0], dep) not in seen_missing:
                    seen_missing.add((chain[0], dep))
                    errs.append(_msg(s, f"'{dep}' is required: {' -> '.join(chain + [dep])}"))
            else:
                walk(dep, chain + [dep], visiting | {dep})

    if exists(c, s["path"]):
        walk(s["path"], [s["path"]], frozenset({s["path"]}))
    return errs


CROSS_TYPES: dict[str, Callable] = {
    "requires_if": x_requires_if, "forbids_if": x_forbids_if, "if_then": x_if_then,
    "all_or_none": x_all_or_none, "at_least_one": x_at_least_one, "exactly_one": x_exactly_one,
    "mutually_exclusive": x_mutually_exclusive, "compare": x_compare, "unique": x_unique,
    "sum": x_sum, "count": x_count, "map": x_map,
}
_NEEDS = {
    "requires_if": {"if", "then_require"}, "forbids_if": {"if", "then_forbid"}, "if_then": {"if", "then"},
    "all_or_none": {"paths"}, "at_least_one": {"paths"}, "exactly_one": {"paths"},
    "mutually_exclusive": {"paths"}, "compare": {"left", "op"}, "unique": {"path"},
    "sum": {"path", "op"}, "count": {"path"}, "map": {"path", "then_path", "table"},
    "depends": {"path", "on"},
}
_OPS = {"<", "<=", ">", ">=", "==", "!="}


def custom(message: str, predicate: Callable[[Any], bool]) -> Rule:
    def rule(c):
        try: return [] if predicate(c) else [message]
        except Exception as e: return [f"{message} (check failed: {e})"]
    return rule


# ───────────── Validator ─────────────

@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    @property
    def ok(self) -> bool: return not self.errors
    def __str__(self) -> str: return "OK" if self.ok else "\n".join(f"- {e}" for e in self.errors)


class ConfigValidator:
    def __init__(self, fields: list[dict], cross: list[dict | Rule] | None = None):
        self.fields, self.cross = fields, cross or []
        self.graph: dict[str, list[str]] = {}
        for s in self.cross:
            if callable(s): continue
            t = s.get("type")
            if t != "depends" and t not in CROSS_TYPES: raise ValueError(f"unknown cross rule type {t!r}")
            if _NEEDS[t] - s.keys(): raise ValueError(f"{t!r} missing keys {sorted(_NEEDS[t] - s.keys())}")
            if t in ("compare", "sum"):
                if s["op"] not in _OPS: raise ValueError(f"bad op {s['op']!r}")
                if t == "compare" and not ({"right", "right_value"} & s.keys()):
                    raise ValueError("compare needs 'right' or 'right_value'")
                if t == "sum" and not ({"right", "right_value"} & s.keys()):
                    raise ValueError("sum needs 'right' or 'right_value'")
            if t == "count" and not ({"min", "max"} & s.keys()): raise ValueError("count needs 'min' or 'max'")
            if t == "depends":
                self.graph.setdefault(s["path"], []).extend(s["on"])
        self._check_cycles()

    def _check_cycles(self):
        state: dict[str, int] = {}
        def dfs(n: str, stack: list[str]):
            state[n] = 1
            for m in self.graph.get(n, []):
                if state.get(m) == 1:
                    raise ValueError("dependency cycle: " + " -> ".join(stack[stack.index(m):] + [m]) if m in stack
                                     else f"dependency cycle at {m!r}")
                if m not in state: dfs(m, stack + [m])
            state[n] = 2
        for n in list(self.graph):
            if n not in state: dfs(n, [n])

    def validate(self, cfg: Any) -> ValidationResult:
        res = ValidationResult()
        for spec in self.fields:
            try: res.errors += check_field(cfg, spec)
            except Exception as e: res.errors.append(f"field rule {spec.get('path')!r} crashed: {e!r}")
        for s in self.cross:
            try:
                if callable(s): res.errors += s(cfg)
                elif s["type"] == "depends": res.errors += x_depends(cfg, s, self.graph)
                else: res.errors += CROSS_TYPES[s["type"]](cfg, s)
            except Exception as e:
                name = "callable" if callable(s) else s["type"]
                res.errors.append(f"cross rule {name} crashed: {e!r}")
        # de-duplicate while keeping order (depends rules share one graph)
        res.errors = list(dict.fromkeys(res.errors))
        return res


# ───────────── Rules as data (replace with yours) ─────────────

FIELDS: list[dict] = [
    {"path": "app.name", "required": True, "type": "str", "min_len": 1, "max_len": 64},
    {"path": "app.env", "required": True, "enum": ["dev", "staging", "prod"]},
    {"path": "app.debug", "type": "bool"},
    {"path": "log.level", "type": "str", "enum": ["debug", "info", "warn", "error"]},
    {"path": "server.host", "required": True, "type": "str"},
    {"path": "server.port", "required": True, "type": "int", "min": 1, "max": 65535},
    {"path": "upstreams.*.host", "required": True, "type": "str"},
    {"path": "upstreams.*.port", "required": True, "type": "int", "min": 1, "max": 65535},
    {"path": "upstreams.*.weight", "type": ["int", "float"], "min": 0},
    {"path": "db.url", "type": "str", "pattern": r"(postgresql|mysql|sqlite)://.+", "pattern_desc": "a supported DB URL"},
    {"path": "db.pool_size", "type": "int", "min": 1, "max": 100},
    {"path": "db.min_pool", "type": "int", "min": 1},
    {"path": "tls.enabled", "type": "bool"},
]

CROSS: list[dict | Rule] = [
    # conditional requirements / prohibitions
    {"type": "requires_if", "if": {"path": "tls.enabled", "eq": True},
     "then_require": ["tls.cert_path", "tls.key_path"]},
    {"type": "forbids_if", "if": {"path": "tls.enabled", "eq": False},
     "then_forbid": ["tls.cert_path", "tls.key_path"]},
    {"type": "if_then", "if": {"path": "app.env", "eq": "prod"}, "then": {"path": "tls.enabled", "eq": True},
     "message": "prod requires tls.enabled = true"},
    {"type": "if_then", "if": {"path": "app.env", "eq": "prod"},
     "then": {"not": {"path": "app.debug", "eq": True}}, "message": "debug must be off in prod"},

    # dependency chains: metrics -> metrics.port -> server.host
    {"type": "depends", "path": "metrics.enabled", "on": ["metrics.port"]},
    {"type": "depends", "path": "metrics.port", "on": ["metrics.path"]},
    {"type": "depends", "path": "metrics.path", "on": ["server.host"]},

    # value-driven dependency
    {"type": "map", "path": "app.env", "then_path": "log.level",
     "table": {"prod": ["warn", "error"], "dev": ["debug", "info"]}},

    # groups
    {"type": "all_or_none", "paths": ["tls.cert_path", "tls.key_path"]},
    {"type": "exactly_one", "paths": ["auth.api_key", "auth.oauth"]},

    # comparisons, aggregates, cardinality, uniqueness
    {"type": "compare", "left": "db.min_pool", "op": "<=", "right": "db.pool_size"},
    {"type": "compare", "left": "upstreams.*.port", "op": "!=", "right": "server.port",
     "message": "an upstream port must differ from server.port"},
    {"type": "sum", "path": "upstreams.*.weight", "op": "<=", "right_value": 100},
    {"type": "count", "path": "upstreams.*", "min": 1, "max": 10},
    {"type": "unique", "path": "upstreams.*.host"},

    custom("db.url required when db.pool_size is set",
           lambda c: not exists(c, "db.pool_size") or exists(c, "db.url")),
]


# ───────────── Self-checks ─────────────

if __name__ == "__main__":
    v = ConfigValidator(FIELDS, CROSS)

    good = {
        "app": {"name": "svc", "env": "prod", "debug": False},
        "log": {"level": "warn"},
        "server": {"host": "0.0.0.0", "port": 8080},
        "upstreams": [{"host": "a", "port": 9001, "weight": 40}, {"host": "b", "port": 9002, "weight": 50}],
        "db": {"url": "postgresql://u:p@h/db", "pool_size": 10, "min_pool": 2},
        "tls": {"enabled": True, "cert_path": "/c.pem", "key_path": "/k.pem"},
        "auth": {"api_key": "abc"},
        "metrics": {"enabled": True, "port": 9100, "path": "/m"},
    }
    assert v.validate(good).ok, v.validate(good)

    bad = {
        "app": {"name": "svc", "env": "prod", "debug": True},
        "log": {"level": "debug"},
        "server": {"host": "h", "port": 80},
        "upstreams": [{"host": "a", "port": 80, "weight": 70}, {"host": "a", "port": 9, "weight": 60}],
        "db": {"pool_size": 5, "min_pool": 9},
        "tls": {"enabled": True, "cert_path": "/c.pem"},
        "auth": {"api_key": "a", "oauth": {}},
        "metrics": {"enabled": True},
    }
    out = "\n".join(v.validate(bad).errors); print("bad:\n" + out)
    for expect in [
        "'tls.key_path' is required when",
        "must be set together",
        "debug must be off in prod",
        "'log.level' must be one of ['warn', 'error'] when 'app.env' is 'prod'",
        "'metrics.port' is required: metrics.enabled -> metrics.port",
        "Exactly one of ['auth.api_key', 'auth.oauth']",
        "'db.min_pool' (9) must be <= 'db.pool_size' (5)",
        "an upstream port must differ from server.port",
        "sum of 'upstreams.*.weight' (130) must be <= 100",
        "'upstreams.1.host' duplicates 'upstreams.0.host'",
        "db.url required when db.pool_size is set",
    ]:
        assert expect in out, f"missing: {expect}"

    # chain continues through present links and stops at the first missing one
    o = "\n".join(v.validate({**good, "metrics": {"enabled": True, "port": 9100}}).errors)
    assert "metrics.enabled -> metrics.port -> metrics.path" in o

    # count bounds
    assert "needs >= 1" in "\n".join(v.validate({**good, "upstreams": []}).errors)

    # bool strictness
    assert not eval_cond({"x": 1}, {"path": "x", "eq": True}) and eval_cond({"x": True}, {"path": "x", "eq": True})
    assert not safe_cmp("<=", True, 5)
    assert "must be a number to be summed" in "\n".join(
        x_sum({"w": [True, 2]}, {"path": "w.*", "op": "<=", "right_value": 9}))

    # construction-time validation, including dependency cycles
    for badrule in [{"type": "nope"}, {"type": "compare", "left": "a", "op": "<"},
                    {"type": "sum", "path": "a", "op": "~", "right_value": 1}, {"type": "count", "path": "a"},
                    [{"type": "depends", "path": "a", "on": ["b"]}, {"type": "depends", "path": "b", "on": ["a"]}]]:
        try:
            ConfigValidator([], badrule if isinstance(badrule, list) else [badrule])
            raise SystemExit(f"should have raised: {badrule}")
        except ValueError:
            pass

    print("all checks passed")