from __future__ import annotations
import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


# ───────────────────────── Path resolution ─────────────────────────

class _Missing:
    def __repr__(self): return "<MISSING>"
    def __bool__(self): return False

MISSING = _Missing()


@dataclass(frozen=True)
class Hit:
    """One resolved location. Exactly one of: value present / MISSING / blocked."""
    path: str
    value: Any = MISSING
    blocked_by: str | None = None      # parent path that isn't a dict/list
    blocked_type: str | None = None

    @property
    def present(self) -> bool:
        return self.value is not MISSING and self.blocked_by is None

    @property
    def blocked(self) -> bool:
        return self.blocked_by is not None


def split_path(path: str) -> list[tuple[str, bool]]:
    """Split 'a.b\\.c.*.0' into [(seg, is_wildcard)]. '\\.' '\\*' '\\\\' escape."""
    segs: list[tuple[str, bool]] = []
    cur: list[str] = []
    escaped = False
    i = 0
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
    """Resolve a path to Hits. Non-wildcard paths always yield exactly one Hit."""
    hits: list[Hit] = [Hit("", cfg)]
    for seg, wild in split_path(path):
        nxt: list[Hit] = []
        for h in hits:
            if not h.present:                       # terminal: carry forward
                nxt.append(h); continue
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
                    nxt.append(Hit(p, node[idx]) if -len(node) <= idx < len(node) else Hit(p))
                except ValueError:
                    nxt.append(Hit(p, MISSING, h.path or "<root>", "list"))
            else:
                nxt.append(Hit(_join(h.path, seg), MISSING, h.path or "<root>", type(node).__name__))
        hits = nxt
    return hits


def get_path(cfg: Any, path: str, default: Any = MISSING) -> Any:
    """First present value at path (back-compat helper), else default."""
    for h in resolve(cfg, path):
        if h.present:
            return h.value
    return default


def exists(cfg: Any, path: str) -> bool:
    return any(h.present for h in resolve(cfg, path))


# ───────────────────────── Type / bool helpers ─────────────────────────

def type_matches(v: Any, types: Iterable[Any]) -> bool:
    """Strict about bool: bool never satisfies int/float; int satisfies float."""
    for t in types:
        if t is None:
            t = type(None)
        if t is bool:
            if isinstance(v, bool): return True
        elif t is int:
            if isinstance(v, int) and not isinstance(v, bool): return True
        elif t is float:
            if isinstance(v, (int, float)) and not isinstance(v, bool): return True
        elif isinstance(v, t):
            return True
    return False


_TRUE, _FALSE = {"true", "yes", "on", "1"}, {"false", "no", "off", "0"}

def as_bool(v: Any, coerce: bool = False) -> bool | None:
    """Return a real bool, or None if v isn't one. With coerce, accept 'true'/'off'/etc. strings."""
    if isinstance(v, bool):
        return v
    if coerce and isinstance(v, str):
        s = v.strip().lower()
        if s in _TRUE: return True
        if s in _FALSE: return False
    return None


def _strict_eq(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def _tn(types) -> str:
    return " or ".join("None" if t is None else t.__name__ for t in types)


def _blocked_msg(h: Hit) -> str:
    return f"'{h.path}' is unreachable: '{h.blocked_by}' is {h.blocked_type}, not an object/list"


# ───────────────────────── Rule factories (cfg -> list[str]) ─────────────────────────

Rule = Callable[[Any], list[str]]


def required(path: str) -> Rule:
    def rule(c):
        return [_blocked_msg(h) if h.blocked else f"'{h.path}' is required"
                for h in resolve(c, path) if not h.present]
    return rule


def type_is(path: str, *types: Any, coerce_bool: bool = False) -> Rule:
    def rule(c):
        errs = []
        for h in resolve(c, path):
            if h.blocked:
                errs.append(_blocked_msg(h)); continue
            if not h.present:
                continue
            ok = type_matches(h.value, types)
            if not ok and coerce_bool and bool in types:
                ok = as_bool(h.value, coerce=True) is not None
            if not ok:
                errs.append(f"'{h.path}' must be {_tn(types)}, got {type(h.value).__name__}")
        return errs
    return rule


def in_range(path: str, lo=None, hi=None) -> Rule:
    def rule(c):
        errs = []
        for h in resolve(c, path):
            if not h.present:
                continue
            v = h.value
            if not type_matches(v, (int, float)) or (isinstance(v, float) and math.isnan(v)):
                errs.append(f"'{h.path}' must be a number, got {type(v).__name__}"
                            + (" (bool is not a number)" if isinstance(v, bool) else ""))
            elif lo is not None and v < lo:
                errs.append(f"'{h.path}' must be >= {lo}, got {v}")
            elif hi is not None and v > hi:
                errs.append(f"'{h.path}' must be <= {hi}, got {v}")
        return errs
    return rule


def length_between(path: str, min_len=0, max_len=None) -> Rule:
    def rule(c):
        errs = []
        for h in resolve(c, path):
            if not h.present or not hasattr(h.value, "__len__"):
                continue
            n = len(h.value)
            if n < min_len: errs.append(f"'{h.path}' length must be >= {min_len}, got {n}")
            elif max_len is not None and n > max_len:
                errs.append(f"'{h.path}' length must be <= {max_len}, got {n}")
        return errs
    return rule


def one_of(path: str, allowed: Iterable[Any]) -> Rule:
    allowed = list(allowed)
    def rule(c):
        return [f"'{h.path}' must be one of {allowed!r}, got {h.value!r}"
                for h in resolve(c, path)
                if h.present and not any(_strict_eq(h.value, a) for a in allowed)]
    return rule


def matches(path: str, pattern: str, desc: str = "") -> Rule:
    rx = re.compile(pattern)
    def rule(c):
        errs = []
        for h in resolve(c, path):
            if not h.present:
                continue
            if not (isinstance(h.value, str) and rx.fullmatch(h.value)):
                errs.append(f"'{h.path}' must match {desc or pattern}, got {h.value!r}")
        return errs
    return rule


def requires(path: str, *others: str, when: Callable[[Any], bool] | None = None) -> Rule:
    """If `path` is present (and `when(value)` holds, if given), every `others` must exist."""
    def rule(c):
        trig = [h for h in resolve(c, path) if h.present and (when is None or when(h.value))]
        if not trig:
            return []
        return [f"'{path}' requires '{o}'" for o in others if not exists(c, o)]
    return rule


def mutually_exclusive(*paths: str) -> Rule:
    def rule(c):
        present = [p for p in paths if exists(c, p)]
        return [f"Only one of {list(paths)} may be set, found {present}"] if len(present) > 1 else []
    return rule


def at_least_one_of(*paths: str) -> Rule:
    def rule(c):
        return [] if any(exists(c, p) for p in paths) else [f"At least one of {list(paths)} must be set"]
    return rule


def custom(message: str, predicate: Callable[[Any], bool]) -> Rule:
    def rule(c):
        try:
            return [] if predicate(c) else [message]
        except Exception as e:
            return [f"{message} (check failed: {e})"]
    return rule


# ───────────────────────── Validator ─────────────────────────

@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def __str__(self) -> str:
        return "OK" if self.ok else "\n".join(f"- {e}" for e in self.errors)


class ConfigValidator:
    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def validate(self, cfg: Any) -> ValidationResult:
        res = ValidationResult()
        for rule in self.rules:
            try:
                res.errors.extend(rule(cfg))
            except Exception as e:  # a buggy rule must not hide other errors
                res.errors.append(f"rule {getattr(rule, '__name__', 'rule')} crashed: {e!r}")
        return res


# ───────────────────────── Example rule set (replace with yours) ─────────────────────────

RULES: list[Rule] = [
    required("app.name"), type_is("app.name", str), length_between("app.name", 1, 64),
    required("app.env"), one_of("app.env", ["dev", "staging", "prod"]),
    type_is("app.debug", bool),

    required("server.host"), type_is("server.host", str),
    required("server.port"), type_is("server.port", int), in_range("server.port", 1, 65535),

    # nested / list / wildcard paths
    type_is("upstreams.*.host", str), required("upstreams.*.port"),
    type_is("upstreams.*.port", int), in_range("upstreams.*.port", 1, 65535),
    type_is("upstreams.0.weight", int, float), in_range("upstreams.*.weight", 0, 100),
    matches(r"labels.app\.kubernetes\.io/name", r"[a-z0-9-]+", "a DNS-style name"),

    type_is("db.url", str),
    matches("db.url", r"(postgresql|mysql|sqlite)://.+", "a supported DB URL"),
    in_range("db.pool_size", 1, 100),

    type_is("tls.enabled", bool),
    requires("tls.enabled", "tls.cert_path", "tls.key_path", when=lambda v: v is True),
    mutually_exclusive("auth.api_key", "auth.oauth"),
    at_least_one_of("auth.api_key", "auth.oauth"),

    custom("prod must have tls.enabled = true",
           lambda c: get_path(c, "app.env") != "prod" or get_path(c, "tls.enabled") is True),
    custom("debug must be false in prod",
           lambda c: get_path(c, "app.env") != "prod" or get_path(c, "app.debug", False) is False),
]


# ───────────────────────── Self-checks ─────────────────────────

if __name__ == "__main__":
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
        "app": {"name": "", "env": "qa", "debug": "yes"},        # str where bool expected
        "server": {"host": "localhost", "port": True},             # bool is not int
        "upstreams": [{"host": "a", "port": 70000}, {"host": 5}],  # wildcard errors by index
        "labels": {"app.kubernetes.io/name": "Bad_Name"},
        "db": {"url": "oracle://x", "pool_size": True},            # bool is not a number
        "tls": {"enabled": True},
        "auth": {"api_key": "a", "oauth": {}},
    }
    blocked = {"app": "oops", "server": {"host": "h", "port": 1}, "auth": {"api_key": "k"}}

    v = ConfigValidator(RULES)
    assert v.validate(good).ok, v.validate(good)
    r = v.validate(bad); print("bad:\n", r)
    assert any("'server.port' must be int, got bool" in e for e in r.errors)
    assert any("'upstreams.0.port' must be <= 65535" in e for e in r.errors)
    assert any("'upstreams.1.port' is required" in e for e in r.errors)
    assert any("'db.pool_size' must be a number" in e for e in r.errors)
    assert any("'labels.app\\.kubernetes\\.io/name'" in e or "app.kubernetes.io/name" in e for e in r.errors)
    rb = v.validate(blocked); print("blocked:\n", rb)
    assert any("'app' is" in e and "not an object/list" in e for e in rb.errors)

    # bool semantics
    assert type_matches(True, (bool,)) and not type_matches(True, (int,))
    assert type_matches(3, (float,)) and not type_matches(True, (float,))
    assert not one_of("x", [1])({"x": True}) == [] and one_of("x", [True])({"x": True}) == []
    assert as_bool("Off", coerce=True) is False and as_bool("off") is None
    assert requires("tls.enabled", "tls.cert_path", when=lambda v: v is True)({"tls": {"enabled": False}}) == []
    print("all checks passed")