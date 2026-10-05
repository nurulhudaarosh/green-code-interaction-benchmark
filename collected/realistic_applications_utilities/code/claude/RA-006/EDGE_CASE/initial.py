from __future__ import annotations
from typing import Any, Callable

_MISSING = object()


def get_path(cfg: Any, path: str, default: Any = None, sep: str = ".") -> Any:
    """Safely traverse nested dicts/lists. Handles None, empty config,
    missing keys, out-of-range list indexes, and non-container values."""
    if cfg is None or path == "":
        return default if cfg is None else cfg
    cur = cfg
    for part in path.split(sep):
        if isinstance(cur, dict):
            cur = cur.get(part, _MISSING)
        elif isinstance(cur, (list, tuple)):
            try:
                cur = cur[int(part)]          # also supports negative indexes
            except (ValueError, IndexError):
                cur = _MISSING
        else:                                  # str, int, None, etc.: can't descend
            cur = _MISSING
        if cur is _MISSING:
            return default
    return default if cur is None else cur


def to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"1", "true", "yes", "on", "y"}:
            return True
        if s in {"0", "false", "no", "off", "n", ""}:
            return False
        raise ValueError(f"not a bool: {v!r}")
    if isinstance(v, (int, float)):
        return bool(v)
    raise ValueError(f"not a bool: {v!r}")


def to_int(v: Any) -> int:
    if isinstance(v, bool):                    # bool is an int subclass; reject it
        raise ValueError("bool is not a valid int here")
    if isinstance(v, float):
        if not v.is_integer():
            raise ValueError(f"lossy float->int: {v}")
        return int(v)
    return int(str(v).strip())                 # "42", " 42 ", 42


def to_float(v: Any) -> float:
    if isinstance(v, bool):
        raise ValueError("bool is not a valid float here")
    f = float(v)
    if f != f or f in (float("inf"), float("-inf")):
        raise ValueError(f"non-finite float: {v}")
    return f


COERCERS: dict[type, Callable[[Any], Any]] = {
    bool: to_bool, int: to_int, float: to_float, str: str,
}


def get_typed(cfg, path, typ, default, lo=None, hi=None, clamp=True):
    """Fetch value, coerce to `typ`, and enforce boundaries.
    Any failure (missing, wrong type, uncoercible) falls back to `default`.
    Out-of-range values are clamped (or default if clamp=False)."""
    raw = get_path(cfg, path, _MISSING)
    if raw is _MISSING:
        return default
    try:
        val = COERCERS[typ](raw)
    except (ValueError, TypeError, KeyError):
        return default
    if typ in (int, float):
        if lo is not None and val < lo:
            val = lo if clamp else default
        if hi is not None and val > hi:
            val = hi if clamp else default
    return val


def deep_merge(base: dict, override: Any) -> dict:
    """Merge override onto base without mutating either.
    Empty / None / non-dict overrides leave defaults intact."""
    out = dict(base)
    if not isinstance(override, dict):
        return out
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif v is not None:                    # None never erases a default
            out[k] = v
    return out


DEFAULTS = {
    "server": {"host": "localhost", "port": 8080, "debug": False},
    "retry": {"attempts": 3, "backoff": 1.5},
    "tags": [],
}


def load_config(user_cfg: Any) -> dict:
    """Normalized, always-valid config from any input (None, {}, junk, partial)."""
    c = deep_merge(DEFAULTS, user_cfg)
    return {
        "host": str(get_path(c, "server.host", "localhost")) or "localhost",
        "port": get_typed(c, "server.port", int, 8080, lo=1, hi=65535),
        "debug": get_typed(c, "server.debug", bool, False),
        "attempts": get_typed(c, "retry.attempts", int, 3, lo=0, hi=10),
        "backoff": get_typed(c, "retry.backoff", float, 1.5, lo=0.0, hi=60.0),
        "first_tag": get_path(c, "tags.0", None),
        "tags": [str(t) for t in c["tags"]] if isinstance(c.get("tags"), list) else [],
    }


if __name__ == "__main__":
    cases = {
        "None":            None,
        "empty dict":      {},
        "wrong top type":  "oops",
        "partial":         {"server": {"port": "9000"}},               # str -> int
        "boundary high":   {"server": {"port": 70000}},                # clamped to 65535
        "boundary low":    {"server": {"port": 0}},                    # clamped to 1
        "mixed types":     {"server": {"port": 80.0, "debug": "yes"},
                            "retry": {"attempts": True, "backoff": "2.5"}},
        "bad values":      {"server": {"port": "abc", "debug": "maybe"},
                            "retry": {"backoff": float("nan")}},
        "null override":   {"server": None, "retry": {"attempts": None}},
        "nested garbage":  {"server": {"host": {"x": 1}}, "tags": "notalist"},
        "list paths":      {"tags": ["a", 2, None]},
    }
    for name, cfg in cases.items():
        print(f"{name:15} -> {load_config(cfg)}")

    # Direct path checks
    print(get_path({"a": [{"b": 1}]}, "a.0.b"))        # 1
    print(get_path({"a": [{"b": 1}]}, "a.5.b", "n/a")) # n/a  (index out of range)
    print(get_path({"a": 5}, "a.b.c", "n/a"))          # n/a  (descending into int)