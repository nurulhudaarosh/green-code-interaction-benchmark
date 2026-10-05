"""Configuration validation: a schema of Field objects checked against a dict or JSON file.

Rules covered
  Types      type / tuple of types (bool never passes as int and vice versa), nullable, safe coercion
  Presence   required, default (value or factory), omitted optional sections, aliases
  Values     choices, min/max (inclusive), gt/lt (exclusive), multiple_of, NaN/inf rejection
  Strings    strip, min_len/max_len, pattern (full match), format (email, url, hostname, ...)
  Containers item schema, unique items, dict-of-values (values / key_pattern), nested schemas
  Cross-field requires, conflicts_with, required_if, forbidden_if, any_of, one_of,
              at_most_one, all_or_none, check(fn)
  Hygiene    unknown fields ("did you mean"), deprecated fields/aliases (warnings), secret
              masking, duplicate JSON keys, env-var overrides (including nested: PREFIX_A__B)
  Schema     contradictory schemas fail fast with ValueError
"""
from __future__ import annotations

import copy
import dataclasses
import difflib
import ipaddress
import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

_MISSING = object()

_INT_RE = re.compile(r"[+-]?[0-9]+")                       # ASCII only: no "1_000", no Arabic digits
_FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_TRUE, _FALSE = {"true", "1", "yes", "on"}, {"false", "0", "no", "off"}
_HOST_LABEL = re.compile(r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)")
_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_PLAIN_KEY = re.compile(r"[A-Za-z_][\w-]*")
_NON_WORD = re.compile(r"\W")      # module level: a backslash in an f-string expression is a
                                   # SyntaxError before Python 3.12


# ------------------------------ Errors ------------------------------

@dataclass(frozen=True)
class Issue:
    path: str          # e.g. "database.pool_size", "hosts[2]", 'labels["a.b"]'; "" = top level
    code: str          # machine-readable: missing, null, type, coerce, choice, min, max, ...
    message: str

    def __str__(self) -> str:
        return f"{self.path or 'top level'}: {self.message}"


class ConfigError(Exception):
    """Raised when validation fails. `.issues` are structured; `.errors` are their strings."""

    def __init__(self, issues: list[Issue]):
        self.issues = list(issues)
        self.errors = [str(i) for i in self.issues]
        super().__init__("Invalid configuration:\n  - " + "\n  - ".join(self.errors))


class _Sink:
    """Collects issues and warnings; len() is the issue count."""
    __slots__ = ("issues", "warnings")

    def __init__(self) -> None:
        self.issues: list[Issue] = []
        self.warnings: list[str] = []

    def add(self, path: str, code: str, message: str) -> None:
        self.issues.append(Issue(path, code, message))

    def warn(self, path: str, message: str) -> None:
        self.warnings.append(f"{path or 'top level'}: {message}")

    def __len__(self) -> int:
        return len(self.issues)


def _join(path: str, key: Any) -> str:
    """Append a key to a path without ambiguity. Plain identifiers use dots; anything else
    (dots, spaces, brackets, empty string) is quoted, so `labels["a.b"]` can never be
    confused with `labels.a.b`. Used for schema keys and data keys alike."""
    key = str(key)
    if _PLAIN_KEY.fullmatch(key):
        return f"{path}.{key}" if path else key
    return f"{path}[{json.dumps(key)}]"


# ------------------------------ Cross-field rules ------------------------------

_RULE_KINDS = {"any_of", "one_of", "at_most_one", "all_or_none", "check"}


@dataclass(frozen=True)
class Rule:
    """A constraint over sibling keys of one dict (top level or a nested section)."""
    kind: str
    fields: tuple[str, ...] = ()
    fn: Callable[[dict[str, Any]], bool] | None = None
    message: str | None = None


def any_of(*fields: str, message: str | None = None) -> Rule:
    """At least one of `fields` must be set."""
    return Rule("any_of", fields, message=message)


def one_of(*fields: str, message: str | None = None) -> Rule:
    """Exactly one of `fields` must be set."""
    return Rule("one_of", fields, message=message)


def at_most_one(*fields: str, message: str | None = None) -> Rule:
    """Zero or one of `fields` may be set."""
    return Rule("at_most_one", fields, message=message)


def all_or_none(*fields: str, message: str | None = None) -> Rule:
    """Either every field is set or none is (e.g. a TLS cert and its key)."""
    return Rule("all_or_none", fields, message=message)


def check(fn: Callable[[dict[str, Any]], bool], message: str) -> Rule:
    """Arbitrary predicate over the validated dict (defaults applied). Fails when it returns False."""
    return Rule("check", fn=fn, message=message)


# ------------------------------ Field ------------------------------

@dataclass
class Field:
    type: Any = None                      # a type or tuple of types
    required: bool = False
    default: Any = _MISSING               # value, or zero-arg callable (called fresh each time)
    nullable: bool = False                # explicit null is allowed
    choices: list[Any] | None = None
    min: float | None = None              # inclusive lower bound
    max: float | None = None              # inclusive upper bound
    gt: float | None = None               # exclusive lower bound
    lt: float | None = None               # exclusive upper bound
    multiple_of: float | None = None
    min_len: int | None = None            # length of str / list / dict
    max_len: int | None = None
    strip: bool = False                   # strip whitespace from strings before checks
    pattern: str | None = None            # regex the whole string must match
    format: str | None = None             # email | url | hostname | ipv4 | ipv6 | ip | uuid | regex
    allow_nonfinite: bool = False         # permit NaN / +-inf floats
    unique: bool = False                  # list items must be distinct
    secret: bool = False                  # never echo the value in messages
    deprecated: str | bool | None = None  # warn when supplied
    aliases: list[str] = field(default_factory=list)   # alternate (old) key names
    validator: Callable[[Any], bool] | None = None     # return False or raise to fail
    message: str | None = None                         # custom message for validator
    schema: dict[str, "Field"] | None = None   # fixed-key nested dict
    item: "Field | None" = None                # list element schema
    values: "Field | None" = None              # arbitrary-key dict: schema for every value
    key_pattern: str | None = None             # regex every key of a `values` dict must match
    coerce: bool = False
    allow_extra: bool = False                  # nested dicts: keep unknown keys
    requires: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    required_if: dict[str, Any] = field(default_factory=dict)   # sibling -> value or predicate
    forbidden_if: dict[str, Any] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)             # group rules for my nested schema


# ------------------------------ Helpers ------------------------------

def _types_of(f: Field) -> tuple[Any, ...]:
    if f.type is None:
        return ()
    return f.type if isinstance(f.type, tuple) else (f.type,)


def _names(types: tuple[Any, ...]) -> str:
    return "/".join(t.__name__ for t in types)


def _is_num(v: Any) -> bool:
    """A real number. bool is a subclass of int in Python, but is never a number here."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _same(a: Any, b: Any) -> bool:
    """Equality that doesn't let True == 1 or False == 0 slip through."""
    return a == b and isinstance(a, bool) == isinstance(b, bool)


def _canon(v: Any) -> Any:
    """Hashable canonical form for duplicate detection; keeps True distinct from 1,
    including inside nested lists and dicts."""
    if isinstance(v, bool):
        return ("b", v)
    if isinstance(v, (int, float)):
        return ("n", v)
    if isinstance(v, str):
        return ("s", v)
    if isinstance(v, (list, tuple)):
        return ("l", tuple(_canon(x) for x in v))
    if isinstance(v, dict):
        return ("d", frozenset((str(k), _canon(x)) for k, x in v.items()))
    return ("o", repr(v))


def _show(value: Any, f: Field) -> str:
    if f.secret:
        return "<hidden>"
    s = repr(value)
    return s if len(s) <= 60 else s[:57] + "..."


def _matches(value: Any, types: tuple[type, ...]) -> bool:
    """isinstance that treats bool as its own type (never an int, and an int is never a bool)
    and lets ints satisfy float."""
    if isinstance(value, bool):
        return bool in types
    if isinstance(value, int) and float in types:
        return True
    return any(isinstance(value, t) for t in types if t is not bool)


def _coerce_one(value: Any, target: type) -> Any:
    """Lossless conversion of a scalar to `target`; raises ValueError otherwise."""
    if target is bool:
        if isinstance(value, str):
            s = value.strip().lower()
            if s in _TRUE:
                return True
            if s in _FALSE:
                return False
        elif _is_int(value) and value in (0, 1):
            return bool(value)
        raise ValueError
    if target is int:
        if isinstance(value, str):
            s = value.strip()
            if _INT_RE.fullmatch(s):
                return int(s)
        elif isinstance(value, float) and value.is_integer():
            return int(value)
        raise ValueError
    if target is float:
        if isinstance(value, str):
            s = value.strip()
            if _FLOAT_RE.fullmatch(s):
                result = float(s)
                if math.isfinite(result):
                    return result
        elif _is_int(value):
            return float(value)                    # OverflowError handled by caller
        raise ValueError
    if target is str:
        if _is_num(value):
            return str(value)
        raise ValueError
    raise ValueError                               # never coerce into list/dict/etc.


def _coerce(value: Any, types: tuple[type, ...], path: str, f: Field, sink: _Sink) -> tuple[Any, bool]:
    if _matches(value, types):
        return value, True
    if isinstance(value, (str, int, float)):       # bool is an int, so it gets a fair try too
        for target in types:
            try:
                return _coerce_one(value, target), True
            except (ValueError, TypeError, OverflowError):
                continue
    sink.add(path, "coerce", f"cannot convert {_show(value, f)} to {_names(types)}")
    return value, False


# ------------------------------ Formats ------------------------------

def _is_hostname(s: str) -> bool:
    return 0 < len(s) <= 253 and all(_HOST_LABEL.fullmatch(p) for p in s.split("."))


def _is_email(s: str) -> bool:
    local, sep, domain = s.rpartition("@")
    return bool(sep and local and not any(c.isspace() for c in local) and "." in domain
                and _is_hostname(domain))


def _is_url(s: str) -> bool:
    from urllib.parse import urlsplit
    if any(c.isspace() for c in s):
        return False
    try:
        parts = urlsplit(s)
        _ = parts.port                      # raises ValueError for an out-of-range port
    except ValueError:
        return False
    return bool(parts.scheme and parts.hostname)


def _ip_ok(cls: Any) -> Callable[[str], bool]:
    def ok(s: str) -> bool:
        try:
            cls(s)
            return True
        except ValueError:
            return False
    return ok


def _is_regex(s: str) -> bool:
    try:
        re.compile(s)
        return True
    except re.error:
        return False


_FORMATS: dict[str, Callable[[str], bool]] = {
    "email": _is_email,
    "url": _is_url,
    "hostname": _is_hostname,
    "ipv4": _ip_ok(ipaddress.IPv4Address),
    "ipv6": _ip_ok(ipaddress.IPv6Address),
    "ip": _ip_ok(ipaddress.ip_address),
    "uuid": lambda s: bool(_UUID_RE.fullmatch(s)),
    "regex": _is_regex,
}


# ------------------------------ Schema sanity ------------------------------

_SIZED = (str, bytes, list, tuple, dict, set, frozenset)


def _check_rules(rules: list[Rule], names: Any, where: str) -> None:
    for r in rules:
        if r.kind not in _RULE_KINDS:
            raise ValueError(f"schema error at {where!r}: unknown rule kind {r.kind!r}")
        if r.kind == "check":
            if not callable(r.fn):
                raise ValueError(f"schema error at {where!r}: check rule needs a callable")
            continue
        if not r.fields:
            raise ValueError(f"schema error at {where!r}: {r.kind} rule names no fields")
        for n in r.fields:
            if n not in names:
                raise ValueError(f"schema error at {where!r}: rule names unknown field {n!r}")


def _check_child(child: Field, where: str, bad: Callable[[str], None]) -> None:
    if (child.required or child.default is not _MISSING or child.requires or child.conflicts_with
            or child.required_if or child.forbidden_if or child.aliases or child.deprecated):
        bad("item/values schema cannot declare required, default, aliases, deprecated or dependencies")
    _check_field(child, f"{where}[]")


def _check_field(f: Field, where: str) -> None:
    """Fail fast (ValueError) on a self-contradictory field definition."""
    def bad(msg: str) -> None:
        raise ValueError(f"schema error at {where!r}: {msg}")

    types = _types_of(f)
    for t in types:
        if not isinstance(t, type):
            bad(f"type must be a class or tuple of classes, got {t!r}")
    if f.required and f.default is not _MISSING:
        bad("required=True and a default contradict each other")
    if f.default is None and not f.nullable:
        bad("default=None requires nullable=True")
    if sum(x is not None for x in (f.schema, f.item, f.values)) > 1:
        bad("a field can have only one of schema, item and values")
    if f.schema is not None and types and dict not in types:
        bad("schema requires type dict")
    if f.values is not None and types and dict not in types:
        bad("values requires type dict")
    if f.item is not None and types and list not in types:
        bad("item requires type list")
    if f.key_pattern is not None and f.values is None:
        bad("key_pattern requires values")
    if f.unique and f.item is None and list not in types:
        bad("unique requires a list field")
    if f.choices is not None and not f.choices:
        bad("choices is empty, so no value could ever be valid")
    if f.rules:                                  # also covers item schemas, which have no key of their own
        if f.schema is None:
            bad("rules require a nested schema")
        _check_rules(f.rules, f.schema, where)

    if (f.pattern is not None or f.format is not None or f.strip) and str not in types:
        bad("pattern/format/strip require type str")
    for label, rx in (("pattern", f.pattern), ("key_pattern", f.key_pattern)):
        if rx is not None:
            try:
                re.compile(rx)
            except re.error as exc:
                bad(f"{label} is not a valid regex ({exc})")
    if f.format is not None and f.format not in _FORMATS:
        bad(f"unknown format {f.format!r}; choose from {sorted(_FORMATS)}")

    bounds = (f.min, f.max, f.gt, f.lt)
    if any(b is not None for b in bounds) or f.multiple_of is not None:
        for b in (*bounds, f.multiple_of):
            if b is not None and (not _is_num(b) or (isinstance(b, float) and math.isnan(b))):
                bad("min/max/gt/lt/multiple_of must be real numbers (not bool, not NaN)")
        if types and not any(issubclass(t, (int, float)) and t is not bool for t in types):
            bad("numeric rules on a non-numeric type")
        if f.multiple_of is not None and not f.multiple_of > 0:
            bad("multiple_of must be positive")
        lows = [(b, ex) for b, ex in ((f.min, False), (f.gt, True)) if b is not None]
        highs = [(b, ex) for b, ex in ((f.max, False), (f.lt, True)) if b is not None]
        for lo, lo_ex in lows:
            for hi, hi_ex in highs:
                if lo > hi or (lo == hi and (lo_ex or hi_ex)):
                    bad(f"bounds admit no value (lower {lo}, upper {hi})")

    for n in (f.min_len, f.max_len):
        if n is not None and (not _is_int(n) or n < 0):
            bad("min_len/max_len must be non-negative integers")
    if f.min_len is not None and f.max_len is not None and f.min_len > f.max_len:
        bad(f"min_len {f.min_len} exceeds max_len {f.max_len}")
    if (f.min_len is not None or f.max_len is not None) and types \
            and not any(issubclass(t, _SIZED) for t in types):
        bad("length bounds on a type without a length")

    if f.schema is not None:
        _check_schema(f.schema, where)
    if f.item is not None:
        _check_child(f.item, where, bad)
    if f.values is not None:
        _check_child(f.values, where, bad)

    # A default is a value like any other: it must satisfy its own constraints.
    if f.default is not _MISSING and f.default is not None:
        try:
            d = f.default() if callable(f.default) else copy.deepcopy(f.default)
        except Exception as exc:
            bad(f"default factory raised {type(exc).__name__}: {exc}")
        probe = _Sink()
        _check_value(d, f, where, probe)
        if probe.issues:
            bad(f"default {_show(d, f)} is invalid ({'; '.join(i.message for i in probe.issues)})")


def _check_schema(schema: dict[str, Field], path: str = "") -> None:
    alias_owner: dict[str, str] = {}
    for key, f in schema.items():
        if not isinstance(key, str):
            raise ValueError(f"schema error at {path or 'top level'!r}: key {key!r} is not a string")
        where = _join(path, key)
        _check_field(f, where)
        for alias in f.aliases:
            if alias in schema or alias in alias_owner:
                raise ValueError(f"schema error at {where!r}: alias {alias!r} collides with another key")
            alias_owner[alias] = key
        deps = (*f.requires, *f.conflicts_with, *f.required_if, *f.forbidden_if)
        for dep in deps:
            if dep not in schema:
                raise ValueError(f"schema error at {where!r}: dependency on unknown sibling {dep!r}")
        if key in deps:
            raise ValueError(f"schema error at {where!r}: field depends on itself")


# ------------------------------ Dependencies ------------------------------

def _condition_holds(result: dict[str, Any], sibling: str, cond: Any) -> bool:
    """A condition on an absent sibling (or a predicate that raises) is simply not met."""
    if sibling not in result:
        return False
    actual = result[sibling]
    if callable(cond):
        try:
            return bool(cond(actual))
        except Exception:
            return False
    return _same(actual, cond)           # required_if={"debug": True} never matches debug == 1


def _describe(cond: dict[str, Any], path: str) -> str:
    return " and ".join(
        f"{_join(path, k)} satisfies a condition" if callable(v) else f"{_join(path, k)} is {v!r}"
        for k, v in cond.items()
    )


def _apply_dependencies(
    config: dict[str, Any], schema: dict[str, Field], result: dict[str, Any],
    rules: list[Rule], path: str, sink: _Sink, before: int,
) -> None:
    """Cross-field checks. "Set" means supplied by the user and not null (False and 0 count)."""
    def is_set(k: str) -> bool:
        return k in config and config[k] is not None

    reported: set[frozenset[str]] = set()
    for key, f in schema.items():
        p = _join(path, key)
        if is_set(key):
            for dep in f.requires:
                if not is_set(dep):
                    sink.add(p, "requires", f"requires {_join(path, dep)} to be set")
            for other in f.conflicts_with:
                pair = frozenset((key, other))
                if is_set(other) and pair not in reported:
                    reported.add(pair)
                    sink.add(p, "conflict", f"cannot be set together with {_join(path, other)}")
            if f.forbidden_if and all(_condition_holds(result, s, c) for s, c in f.forbidden_if.items()):
                sink.add(p, "forbidden", f"must not be set when {_describe(f.forbidden_if, path)}")
        elif f.required_if and all(_condition_holds(result, s, c) for s, c in f.required_if.items()):
            sink.add(p, "required_if", f"required when {_describe(f.required_if, path)}")

    for rule in rules:
        names = ", ".join(_join(path, n) for n in rule.fields)
        given = [n for n in rule.fields if is_set(n)]
        got = ", ".join(_join(path, g) for g in given)
        msg: str | None = None
        if rule.kind == "any_of" and not given:
            msg = rule.message if rule.message is not None else f"at least one of {names} is required"
        elif rule.kind == "one_of" and len(given) != 1:
            msg = rule.message if rule.message is not None else (
                f"exactly one of {names} is required" if not given
                else f"only one of {names} may be set (got {got})")
        elif rule.kind == "at_most_one" and len(given) > 1:
            msg = rule.message if rule.message is not None else f"at most one of {names} may be set (got {got})"
        elif rule.kind == "all_or_none" and given and len(given) != len(rule.fields):
            missing = ", ".join(_join(path, n) for n in rule.fields if n not in given)
            msg = rule.message if rule.message is not None else f"{names} must be set together (missing {missing})"
        elif rule.kind == "check":
            try:
                if rule.fn(result) is False:
                    msg = rule.message
            except Exception as exc:
                # A predicate tripping over data that is already reported is a cascade.
                if len(sink) == before:
                    msg = f"{rule.message} ({type(exc).__name__}: {exc})"
        if msg is not None:
            sink.add(path, "rule", msg)


# ------------------------------ Core validation ------------------------------

def _check_value(value: Any, f: Field, path: str, sink: _Sink) -> Any:
    """Entry point for any value: handles explicit null, then full validation."""
    if value is None:
        if not f.nullable:
            sink.add(path, "null", "must not be null")
        return None
    return _validate_value(value, f, path, sink)


def _multiple_ok(value: Any, step: Any) -> bool:
    try:
        if _is_int(value) and _is_int(step):
            return value % step == 0
        q = value / step
        return math.isclose(q, round(q), rel_tol=0.0, abs_tol=1e-9)
    except (OverflowError, ValueError, ZeroDivisionError):   # inf / nan
        return False


def _validate_value(value: Any, f: Field, path: str, sink: _Sink) -> Any:
    types = _types_of(f)

    if f.coerce and types:
        value, ok = _coerce(value, types, path, f, sink)
        if not ok:
            return value

    if types:
        if not _matches(value, types):
            sink.add(path, "type", f"expected {_names(types)}, got {type(value).__name__}")
            return value
        if float in types and int not in types and _is_int(value):
            try:
                value = float(value)
            except OverflowError:
                sink.add(path, "type", "integer is too large to represent as float")
                return value

    if f.strip and isinstance(value, str):
        value = value.strip()

    # NaN compares False against everything, so it would sail through every bound.
    if isinstance(value, float) and not math.isfinite(value) and not f.allow_nonfinite:
        sink.add(path, "nonfinite", f"must be a finite number, got {value!r}")
        return value

    for label, sub, kind in (("dict", f.schema, dict), ("list", f.item, list), ("dict", f.values, dict)):
        if sub is not None and not isinstance(value, kind):
            sink.add(path, "type", f"expected {label}, got {type(value).__name__}")
            return value

    if f.choices is not None and not any(_same(value, c) for c in f.choices):
        sink.add(path, "choice", f"{_show(value, f)} not in allowed values {f.choices}")

    if _is_num(value):
        if f.min is not None and value < f.min:
            sink.add(path, "min", f"{_show(value, f)} is below minimum {f.min}")
        if f.max is not None and value > f.max:
            sink.add(path, "max", f"{_show(value, f)} is above maximum {f.max}")
        if f.gt is not None and not value > f.gt:
            sink.add(path, "gt", f"{_show(value, f)} must be greater than {f.gt}")
        if f.lt is not None and not value < f.lt:
            sink.add(path, "lt", f"{_show(value, f)} must be less than {f.lt}")
        if f.multiple_of is not None and not _multiple_ok(value, f.multiple_of):
            sink.add(path, "multiple_of", f"{_show(value, f)} is not a multiple of {f.multiple_of}")

    if hasattr(value, "__len__"):
        if f.min_len is not None and len(value) < f.min_len:
            sink.add(path, "length", f"length {len(value)} is below minimum {f.min_len}")
        if f.max_len is not None and len(value) > f.max_len:
            sink.add(path, "length", f"length {len(value)} is above maximum {f.max_len}")

    if isinstance(value, str):
        if f.pattern is not None and not re.fullmatch(f.pattern, value):
            sink.add(path, "pattern", f"does not match pattern {f.pattern!r}")
        if f.format is not None and not _FORMATS[f.format](value):
            sink.add(path, "format", f"is not a valid {f.format}")

    if f.validator is not None:
        try:
            if f.validator(value) is False:
                sink.add(path, "validator", f.message or "failed custom validation")
        except Exception as exc:
            sink.add(path, "validator", f.message or ("failed custom validation" if f.secret else str(exc)))

    if f.schema is not None:
        value = _validate_dict(value, f.schema, path, sink, f.allow_extra, f.rules)
    elif f.item is not None:
        value = [_check_value(v, f.item, f"{path}[{i}]", sink) for i, v in enumerate(value)]
        if f.unique:
            seen: dict[Any, int] = {}
            for i, v in enumerate(value):
                first = seen.setdefault(_canon(v), i)
                if first != i:
                    sink.add(f"{path}[{i}]", "unique", f"duplicate of {path}[{first}]")
    elif f.values is not None:
        out: dict[Any, Any] = {}
        for k, v in value.items():
            kp = _join(path, k)
            if not isinstance(k, str):
                sink.add(kp, "key", "key must be a string")
                continue
            if f.key_pattern is not None and not re.fullmatch(f.key_pattern, k):
                sink.add(kp, "key", f"key does not match pattern {f.key_pattern!r}")
            out[k] = _check_value(v, f.values, kp, sink)
        value = out

    return value


def _resolve_aliases(config: dict[str, Any], schema: dict[str, Field], path: str, sink: _Sink) -> dict[str, Any]:
    if not any(f.aliases for f in schema.values()):
        return config
    out = dict(config)
    for key, f in schema.items():
        for alias in f.aliases:
            if alias not in out:
                continue
            if key in out:
                sink.add(_join(path, alias), "alias_conflict",
                         f"is an alias of {_join(path, key)}; set only one of them")
                del out[alias]
            else:
                out[key] = out.pop(alias)
                sink.warn(_join(path, alias), f"is an alias; use {_join(path, key)} instead")
    return out


def _validate_dict(
    config: dict[str, Any], schema: dict[str, Field], path: str, sink: _Sink,
    allow_extra: bool, rules: list[Rule] | None = None,
) -> dict[str, Any]:
    before = len(sink)
    config = _resolve_aliases(config, schema, path, sink)
    result: dict[str, Any] = {}

    for key, f in schema.items():
        p = _join(path, key)
        if key in config:
            if f.deprecated:
                sink.warn(p, f.deprecated if isinstance(f.deprecated, str) else "is deprecated")
            result[key] = _check_value(config[key], f, p, sink)
        elif f.default is not _MISSING:
            d = f.default
            result[key] = d() if callable(d) else copy.deepcopy(d)
        elif f.required:
            sink.add(p, "missing", "required field is missing")
        elif f.schema is not None:
            # Optional section omitted: fill nested defaults only if that succeeds on its own;
            # unmet required children must not create errors for an unused section.
            scratch = _Sink()
            nested = _validate_dict({}, f.schema, p, scratch, f.allow_extra, f.rules)
            if not scratch.issues:
                result[key] = nested

    extras = sorted(set(config) - set(schema), key=str)
    if allow_extra:
        for k in extras:
            result[k] = copy.deepcopy(config[k])
    else:
        known = [str(k) for k in schema] + [a for f in schema.values() for a in f.aliases]
        for k in extras:
            hint = difflib.get_close_matches(str(k), known, n=1)
            tip = f" (did you mean {hint[0]!r}?)" if hint else ""
            sink.add(_join(path, k), "unknown", f"unknown field{tip}")

    _apply_dependencies(config, schema, result, rules or [], path, sink, before)
    return result


def validate(
    config: Any,
    schema: dict[str, Field],
    *,
    allow_extra: bool = False,
    rules: list[Rule] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Validate `config` against `schema`; return a new dict with defaults applied.

    Raises ConfigError listing every problem at once, and ValueError if the schema itself
    is inconsistent. Non-fatal notices (deprecations, aliases) are appended to `warnings`.
    """
    _check_schema(schema)
    _check_rules(rules or [], schema, "top level")
    if not isinstance(config, dict):
        raise ConfigError([Issue("", "type", f"expected dict, got {type(config).__name__}")])
    sink = _Sink()
    try:
        result = _validate_dict(config, schema, "", sink, allow_extra, rules)
    except RecursionError:
        raise ConfigError([Issue("", "depth", "configuration is nested too deeply")]) from None
    if warnings is not None:
        warnings.extend(sink.warnings)
    if sink.issues:
        raise ConfigError(sink.issues)
    return result


# ------------------------------ Loading ------------------------------

class _DuplicateKey(ValueError):
    pass


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise _DuplicateKey(k)
        out[k] = v
    return out


def _env_key(key: str) -> str:
    return _NON_WORD.sub("_", str(key)).upper()


def _is_structured(f: Field) -> bool:
    return (f.schema is not None or f.item is not None or f.values is not None
            or any(t in (dict, list) for t in _types_of(f)))


def _overlay_env(
    raw: dict[str, Any], schema: dict[str, Field], name_prefix: str, delim: str,
    skip_empty: bool, issues: list[Issue],
) -> tuple[dict[str, Field], bool]:
    """Apply env overrides to `raw` in place, at every nesting level of the schema.

    PREFIX_DATABASE='{"url": ...}' replaces a whole section (JSON); PREFIX_DATABASE__POOL_SIZE=20
    sets one nested key. Returns a copy of `schema` in which overridden leaves have coerce=True
    (env values are strings) and whether anything changed. The caller's schema is never mutated.
    """
    effective = dict(schema)
    changed = False
    for key, f in schema.items():
        name = f"{name_prefix}{_env_key(key)}"
        val = os.environ.get(name)
        if val is not None and not (skip_empty and val == ""):
            changed = True
            for alias in f.aliases:
                raw.pop(alias, None)                     # env wins over an old name in the file
            if _is_structured(f):
                try:
                    raw[key] = json.loads(val)
                except json.JSONDecodeError as exc:
                    issues.append(Issue(name, "env", f"invalid JSON ({exc})"))
            else:
                raw[key] = val
                effective[key] = dataclasses.replace(f, coerce=True)
        if f.schema is not None:
            existing = raw.get(key)
            if existing is None or isinstance(existing, dict):
                section = existing if isinstance(existing, dict) else {}
                child_schema, child_changed = _overlay_env(
                    section, f.schema, name + delim, delim, skip_empty, issues)
                if child_changed:
                    changed = True
                    raw[key] = section
                    effective[key] = dataclasses.replace(effective[key], schema=child_schema)
            # a non-dict section is left alone; validation reports the type error
    return effective, changed


def load_config(
    path: str,
    schema: dict[str, Field],
    env_prefix: str = "",
    *,
    rules: list[Rule] | None = None,
    warnings: list[str] | None = None,
    empty_env_is_unset: bool = True,
    env_delimiter: str = "__",
) -> dict[str, Any]:
    """Load JSON, overlay env vars, then validate.

    Env names are `<env_prefix><KEY>`; nested keys join with `env_delimiter`
    (APP_DATABASE__POOL__SIZE). Env values override the file (and any alias of the same key).
    Structured fields take JSON in the env var; everything else is coerced from a string.
    Duplicate JSON keys are an error rather than "last one wins".
    """
    try:
        with open(path, encoding="utf-8-sig") as fh:          # tolerate a UTF-8 BOM
            raw = json.load(fh, object_pairs_hook=_no_duplicates)
    except FileNotFoundError:
        raise ConfigError([Issue(path, "file", "config file not found")]) from None
    except UnicodeDecodeError:
        raise ConfigError([Issue(path, "file", "file is not valid UTF-8")]) from None
    except _DuplicateKey as exc:
        raise ConfigError([Issue(path, "duplicate_key", f"duplicate key {exc.args[0]!r}")]) from None
    except json.JSONDecodeError as exc:                       # includes empty files
        raise ConfigError([Issue(path, "file", f"invalid JSON ({exc})")]) from None
    except RecursionError:
        raise ConfigError([Issue(path, "depth", "JSON is nested too deeply")]) from None
    except OSError as exc:                                    # directory, permissions, ...
        raise ConfigError([Issue(path, "file", f"cannot read file ({exc.strerror or exc})")]) from None
    if not isinstance(raw, dict):
        raise ConfigError([Issue(path, "file", "top level must be an object")])

    env_issues: list[Issue] = []
    effective = schema
    if env_prefix:
        effective, _ = _overlay_env(raw, schema, env_prefix, env_delimiter, empty_env_is_unset, env_issues)

    try:
        result = validate(raw, effective, rules=rules, warnings=warnings)
    except ConfigError as exc:
        raise ConfigError(env_issues + exc.issues) from None
    if env_issues:
        raise ConfigError(env_issues)
    return result


# ------------------------------- Example + self-check -------------------------------
if __name__ == "__main__":
    import tempfile

    SCHEMA = {
        "app_name": Field(str, required=True, min_len=1, strip=True, pattern=r"[A-Za-z][\w-]*"),
        "env": Field(str, default="dev", choices=["dev", "staging", "prod"]),
        "port": Field(int, default=8000, min=1, max=65535, coerce=True, aliases=["listen_port"]),
        "ratio": Field(float, default=0.5, gt=0, max=1),
        "batch": Field(int, default=10, min=5, multiple_of=5),
        "admin_email": Field(str, format="email", nullable=True, default=None),
        "api_key": Field(str, secret=True, min_len=8, pattern=r"[A-Za-z0-9]+", required_if={"env": "prod"}),
        "debug": Field(bool, default=False, forbidden_if={"env": "prod"}),
        "verbose": Field(bool, default=False),
        "legacy_mode": Field(bool, deprecated="use 'env' instead"),
        "flags": Field(list, default=list, unique=True, item=Field(bool)),
        "allowed_hosts": Field(list, default=list, unique=True, max_len=3, item=Field(str, format="hostname")),
        "labels": Field(dict, default=dict, key_pattern=r"[a-z_.]+", values=Field(str, max_len=10)),
        "tls_cert": Field(str, requires=["tls_key"]),
        "tls_key": Field(str, requires=["tls_cert"]),
        "database": Field(
            dict,
            required=True,
            schema={
                "url": Field(str, format="url"),
                "host": Field(str, format="hostname"),
                "port": Field(int, default=5432, min=1, max=65535),
                "pool": Field(dict, schema={"size": Field(int, default=5, min=1, max=100),
                                            "ssl": Field(bool, default=True)}),
            },
            rules=[one_of("url", "host", message="provide either url or host")],
        ),
    }
    RULES = [check(lambda c: not (c["env"] == "prod" and c["port"] == 80), "prod must not use port 80")]

    def issue_paths(cfg: Any) -> set[str]:
        try:
            validate(cfg, SCHEMA, rules=RULES)
        except ConfigError as e:
            return {i.path for i in e.issues}
        return set()

    def show(title: str, cfg: Any) -> None:
        print(f"--- {title} ---")
        warns: list[str] = []
        try:
            print(validate(cfg, SCHEMA, rules=RULES, warnings=warns))
        except ConfigError as e:
            print(e)
        for w in warns:
            print("  warning:", w)
        print()

    show("valid (alias + deprecated field produce warnings, not errors)",
         {"app_name": " demo ", "listen_port": "9000", "legacy_mode": True,
          "allowed_hosts": ["a.example.com"], "database": {"host": "db.local"}})

    show("empty config: every missing field at once", {})

    booleans_and_paths = {
        "app_name": "demo",
        "debug": 1,                                          # int is not a bool
        "verbose": "true",                                   # str is not a bool (coerce is off)
        "port": True,                                        # bool is not an int
        "ratio": False,                                      # ...nor a float
        "flags": [True, 1, True],                            # 1 is not a bool; only index 2 duplicates
        "labels": {"a.b": "x", "Bad key": "y"},              # keys are quoted in paths
        "database": {"host": "h", "port": False, "pool": {"size": True, "ssl": "yes"}},
        "databse": {},                                       # typo -> suggestion
    }
    show("nested paths and booleans", booleans_and_paths)

    expected = {"debug", "verbose", "port", "ratio", "flags[1]", "flags[2]", 'labels["Bad key"]',
                "database.port", "database.pool.size", "database.pool.ssl", "databse"}
    got = issue_paths(booleans_and_paths)
    assert expected <= got, f"missing expected issues: {expected - got}"
    assert "labels.a.b" not in got and 'labels["a.b"]' not in got   # "a.b" is a valid key

    show("one problem per rule", {
        "app_name": "9lives", "env": "prod", "debug": True, "port": 80, "listen_port": 81,
        "batch": 12, "admin_email": "not-an-email", "api_key": "pa$$",
        "allowed_hosts": ["a.com", "a.com", "bad_host!"], "tls_cert": "/c.pem",
        "database": {"url": "x", "host": "y"},
    })

    print("--- env overrides reach nested keys (APP_DATABASE__POOL__SIZE) and coerce strings ---")
    env_names = ("APP_VERBOSE", "APP_DATABASE__PORT", "APP_DATABASE__POOL__SIZE", "APP_DATABASE__POOL__SSL")
    try:
        with tempfile.TemporaryDirectory() as d:
            cfg_path = os.path.join(d, "config.json")
            with open(cfg_path, "w", encoding="utf-8") as fh:
                json.dump({"app_name": "demo", "database": {"host": "db.local", "pool": {"size": 5}}}, fh)
            os.environ.update({"APP_VERBOSE": "yes", "APP_DATABASE__PORT": "6543",
                               "APP_DATABASE__POOL__SIZE": "20", "APP_DATABASE__POOL__SSL": "off"})
            cfg = load_config(cfg_path, SCHEMA, env_prefix="APP_", rules=RULES)
            print(cfg)
            assert cfg["verbose"] is True and cfg["database"]["port"] == 6543
            assert cfg["database"]["pool"] == {"size": 20, "ssl": False}
            assert SCHEMA["verbose"].coerce is False          # caller's schema untouched

            os.environ["APP_DATABASE__POOL__SIZE"] = "huge"
            try:
                load_config(cfg_path, SCHEMA, env_prefix="APP_", rules=RULES)
                raise AssertionError("expected ConfigError")
            except ConfigError as e:
                print(e)
                assert [i.path for i in e.issues] == ["database.pool.size"]
    finally:
        for n in env_names:
            os.environ.pop(n, None)
    print()

    print("--- contradictory schema fails fast ---")
    try:
        validate({}, {"n": Field(int, default=True)})
        raise AssertionError("expected ValueError")
    except ValueError as e:
        print(e)
    print("\nself-checks passed")