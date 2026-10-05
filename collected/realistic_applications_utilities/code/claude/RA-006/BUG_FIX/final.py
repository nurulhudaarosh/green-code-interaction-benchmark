from __future__ import annotations
import math
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
    """Non-wildcard paths always yield exactly one Hit (present, missing, or blocked)."""
    hits = [Hit("", cfg)]
    for seg, wild in split_path(path):
        nxt: list[Hit] = []
        for h in hits:
            if h.blocked:
                nxt.append(h); continue
            if not h.present:                      # missing parent: extend path for clear messages
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


def get_path(cfg: Any, path: str, default: Any = None) -> Any:
    for h in resolve(cfg, path):
        if h.present:
            return h.value
    return default


def exists(cfg: Any, path: str) -> bool:
    return any(h.present for h in resolve(cfg, path))


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


# ───────────── Rule engine ─────────────

Rule = Callable[[Any], list[str]]


def _blocked(h: Hit) -> str:
    return f"'{h.path}' is unreachable: '{h.blocked_by}' is {h.blocked_type}, not an object/list"


def check_field(c: Any, spec: dict) -> list[str]:
    errs: list[str] = []
    types = [TYPES[t] for t in ([spec["type"]] if isinstance(spec.get("type"), str) else spec.get("type", []))]
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
            if not type_matches(v, (int, float)) or (isinstance(v, float) and math.isnan(v)):
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

        if "requires" in spec and ("when" not in spec or strict_eq(v, spec["when"])):
            errs += [f"'{p}' requires '{o}'" for o in spec["requires"] if not exists(c, o)]
    return errs


def mutually_exclusive(*paths: str) -> Rule:
    def rule(c):
        found = [p for p in paths if exists(c, p)]
        return [f"Only one of {list(paths)} may be set, found {found}"] if len(found) > 1 else []
    return rule


def at_least_one_of(*paths: str) -> Rule:
    return lambda c: [] if any(exists(c, p) for p in paths) else [f"At least one of {list(paths)} must be set"]


def custom(message: str, predicate: Callable[[Any], bool]) -> Rule:
    def rule(c):
        try:
            return [] if predicate(c) else [message]
        except Exception as e:
            return [f"{message} (check failed: {e})"]
    return rule


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    @property
    def ok(self) -> bool: return not self.errors
    def __str__(self) -> str: return "OK" if self.ok else "\n".join(f"- {e}" for e in self.errors)


class ConfigValidator:
    def __init__(self, fields: list[dict], cross: list[Rule] | None = None):
        self.fields, self.cross = fields, cross or []

    def validate(self, cfg: Any) -> ValidationResult:
        res = ValidationResult()
        for spec in self.fields:
            try: res.errors += check_field(cfg, spec)
            except Exception as e: res.errors.append(f"field rule {spec.get('path')!r} crashed: {e!r}")
        for rule in self.cross:
            try: res.errors += rule(cfg)
            except Exception as e: res.errors.append(f"cross rule crashed: {e!r}")
        return res


# ───────────── Rules as data (replace with yours) ─────────────

FIELDS: list[dict] = [
    {"path": "app.name", "required": True, "type": "str", "min_len": 1, "max_len": 64},
    {"path": "app.env", "required": True, "enum": ["dev", "staging", "prod"]},
    {"path": "app.debug", "type": "bool"},
    {"path": "server.host", "required": True, "type": "str"},
    {"path": "server.port", "required": True, "type": "int", "min": 1, "max": 65535},
    {"path": "upstreams.*.host", "required": True, "type": "str"},
    {"path": "upstreams.*.port", "required": True, "type": "int", "min": 1, "max": 65535},
    {"path": "upstreams.*.weight", "type": ["int", "float"], "min": 0, "max": 100},
    {"path": r"labels.app\.kubernetes\.io/name", "pattern": r"[a-z0-9-]+", "pattern_desc": "a DNS-style name"},
    {"path": "db.url", "type": "str", "pattern": r"(postgresql|mysql|sqlite)://.+", "pattern_desc": "a supported DB URL"},
    {"path": "db.pool_size", "type": "int", "min": 1, "max": 100},
    {"path": "tls.enabled", "type": "bool", "requires": ["tls.cert_path", "tls.key_path"], "when": True},
]

CROSS: list[Rule] = [
    mutually_exclusive("auth.api_key", "auth.oauth"),
    at_least_one_of("auth.api_key", "auth.oauth"),
    custom("prod must have tls.enabled = true",
           lambda c: get_path(c, "app.env") != "prod" or get_path(c, "tls.enabled") is True),
    custom("debug must be false in prod",
           lambda c: get_path(c, "app.env") != "prod" or get_path(c, "app.debug", False) is False),
]


# ───────────── Self-checks ─────────────

if __name__ == "__main__":
    v = ConfigValidator(FIELDS, CROSS)

    good = {
        "app": {"name": "svc", "env": "prod", "debug": False},
        "server": {"host": "0.0.0.0", "port": 8080},
        "upstreams": [{"host": "a", "port": 1, "weight": 2.5}, {"host": "b", "port": 2}],
        "labels": {"app.kubernetes.io/name": "my-app"},
        "db": {"url": "postgresql://u:p@localhost/db", "pool_size": 10},
        "tls": {"enabled": True, "cert_path": "/c.pem", "key_path": "/k.pem"},
        "auth": {"api_key": "abc"},
    }
    bad = {
        "app": {"name": "", "env": "qa", "debug": "yes"},
        "server": {"host": "localhost", "port": True},
        "upstreams": [{"host": "a", "port": 70000}, {"host": 5}],
        "labels": {"app.kubernetes.io/name": "Bad_Name"},
        "db": {"url": "oracle://x", "pool_size": True},
        "tls": {"enabled": True},
        "auth": {"api_key": "a", "oauth": {}},
    }
    blocked = {"app": "oops", "server": {"host": "h", "port": 1}, "auth": {"api_key": "k"}}

    assert v.validate(good).ok, v.validate(good)

    r = v.validate(bad); print("bad:\n", r)
    msgs = "\n".join(r.errors)
    assert "'server.port' must be int, got bool" in msgs
    assert "'upstreams.0.port' must be <= 65535" in msgs
    assert "'upstreams.1.port' is required" in msgs
    assert "'upstreams.1.host' must be str, got int" in msgs
    assert "'db.pool_size' must be int, got bool" in msgs
    assert "'app.debug' must be bool, got str" in msgs
    assert "labels.app\\.kubernetes\\.io/name" in msgs

    rb = v.validate(blocked); print("blocked:\n", rb)
    assert any("'app' is str, not an object/list" in e for e in rb.errors)

    # missing parent reports the full path
    assert "'app.name' is required" in str(v.validate({}))

    # bool semantics
    assert type_matches(True, (bool,)) and not type_matches(True, (int,))
    assert not type_matches(1, (bool,)) and not type_matches(True, (float,))
    assert check_field({"x": True}, {"path": "x", "enum": [1]}) != []
    assert check_field({"x": True}, {"path": "x", "enum": [True]}) == []
    assert check_field({"x": True}, {"path": "x", "min": 0}) != []
    assert as_bool("Off", coerce=True) is False and as_bool("off") is None
    assert check_field({"tls": {"enabled": "off"}},
                       {"path": "tls.enabled", "type": "bool", "coerce_bool": True}) == []
    assert check_field({"tls": {"enabled": False}},
                       {"path": "tls.enabled", "requires": ["tls.cert_path"], "when": True}) == []

    # list index / negative index / escaped keys
    cfg = {"items": [{"id": 1}, {"id": 2}], "a.b": {"c": 3}}
    assert get_path(cfg, "items.-1.id") == 2 and get_path(cfg, r"a\.b.c") == 3
    print("all checks passed")