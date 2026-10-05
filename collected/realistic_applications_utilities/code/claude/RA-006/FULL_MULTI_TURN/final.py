from __future__ import annotations

import copy
import dataclasses
import json
import math
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

_MISSING = object()

_INT_RE = re.compile(r"[+-]?[0-9]+")                                   # ASCII only: no "1_000", no "٣"
_FLOAT_RE = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_TRUE, _FALSE = {"true", "1", "yes"}, {"false", "0", "no"}


class ConfigError(Exception):
    """Raised when validation fails; holds every error found, not just the first."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid configuration:\n  - " + "\n  - ".join(errors))


# ------------------------------ Dependencies ------------------------------

@dataclass(frozen=True)
class Rule:
    """A cross-field constraint over sibling keys of one dict (top level or nested)."""
    kind: str                                   # any_of | one_of | all_or_none | check
    fields: tuple[str, ...] = ()
    fn: Callable[[dict[str, Any]], bool] | None = None
    message: str | None = None


def any_of(*fields: str, message: str | None = None) -> Rule:
    """At least one of `fields` must be set."""
    return Rule("any_of", fields, message=message)


def one_of(*fields: str, message: str | None = None) -> Rule:
    """Exactly one of `fields` must be set."""
    return Rule("one_of", fields, message=message)


def all_or_none(*fields: str, message: str | None = None) -> Rule:
    """Either every field is set or none is (e.g. a TLS cert and its key)."""
    return Rule("all_or_none", fields, message=message)


def check(fn: Callable[[dict[str, Any]], bool], message: str) -> Rule:
    """Arbitrary predicate over the validated dict (defaults applied)."""
    return Rule("check", fn=fn, message=message)


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
    min_len: int | None = None
    max_len: int | None = None
    strip: bool = False                   # strip whitespace from strings before checks
    allow_nonfinite: bool = False         # permit NaN / +-inf floats
    validator: Callable[[Any], bool] | None = None
    message: str | None = None
    schema: dict[str, "Field"] | None = None   # nested dict schema (value must be a dict)
    item: "Field | None" = None                # list item schema (value must be a list)
    coerce: bool = False
    allow_extra: bool = False
    requires: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    required_if: dict[str, Any] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)


# ------------------------------ Type helpers ------------------------------

def _types_of(f: Field) -> tuple[Any, ...]:
    if f.type is None:
        return ()
    return f.type if isinstance(f.type, tuple) else (f.type,)


def _names(types: tuple[Any, ...]) -> str:
    return "/".join(t.__name__ for t in types)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _same(a: Any, b: Any) -> bool:
    """Equality that doesn't let True == 1 or False == 0 slip through."""
    return a == b and isinstance(a, bool) == isinstance(b, bool)


def _matches(value: Any, types: tuple[type, ...]) -> bool:
    """isinstance that treats bool as its own type and lets ints satisfy float."""
    if isinstance(value, bool):
        return bool in types
    if isinstance(value, int) and float in types:
        return True
    return isinstance(value, types)


def _coerce_one(value: Any, target: type) -> Any:
    """Lossless conversion of a scalar to `target`; raises ValueError otherwise."""
    if target is bool:
        if isinstance(value, str):
            s = value.strip().lower()
            if s in _TRUE:
                return True
            if s in _FALSE:
                return False
        elif isinstance(value, int) and not isinstance(value, bool) and value in (0, 1):
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
                if math.isfinite(result):          # "1e999" overflows to inf: reject
                    return result
        elif isinstance(value, int) and not isinstance(value, bool):
            return float(value)                    # may raise OverflowError, handled by caller
        raise ValueError
    if target is str:
        if _is_num(value):
            return str(value)
        raise ValueError
    raise ValueError


def _coerce(value: Any, types: tuple[type, ...], path: str, errors: list[str]) -> tuple[Any, bool]:
    if _matches(value, types):
        return value, True
    if isinstance(value, (str, int, float)):
        for target in types:
            try:
                return _coerce_one(value, target), True
            except (ValueError, TypeError, OverflowError):
                continue
    shown = value if not isinstance(value, str) or len(value) <= 40 else value[:37] + "..."
    errors.append(f"{path}: cannot convert {shown!r} to {_names(types)}")
    return value, False


# ------------------------------ Schema sanity ------------------------------

_SIZED = (str, bytes, list, tuple, dict, set, frozenset)


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
    if f.schema is not None and f.item is not None:
        bad("a field cannot have both schema and item")
    if f.schema is not None and types and dict not in types:
        bad("schema requires type dict")
    if f.item is not None and types and list not in types:
        bad("item requires type list")
    if f.choices is not None and not f.choices:
        bad("choices is empty, so no value could ever be valid")

    bounds = (f.min, f.max, f.gt, f.lt)
    if any(b is not None for b in bounds):
        if any(not _is_num(b) for b in bounds if b is not None):
            bad("min/max/gt/lt must be numbers")
        if types and not any(issubclass(t, (int, float)) for t in types):
            bad("numeric bounds on a non-numeric type")
        lows = [(b, ex) for b, ex in ((f.min, False), (f.gt, True)) if b is not None]
        highs = [(b, ex) for b, ex in ((f.max, False), (f.lt, True)) if b is not None]
        for lo, lo_ex in lows:
            for hi, hi_ex in highs:
                if lo > hi or (lo == hi and (lo_ex or hi_ex)):
                    bad(f"bounds admit no value (lower {lo}, upper {hi})")

    for n in (f.min_len, f.max_len):
        if n is not None and (isinstance(n, bool) or not isinstance(n, int) or n < 0):
            bad("min_len/max_len must be non-negative integers")
    if f.min_len is not None and f.max_len is not None and f.min_len > f.max_len:
        bad(f"min_len {f.min_len} exceeds max_len {f.max_len}")
    if (f.min_len is not None or f.max_len is not None) and types \
            and not any(issubclass(t, _SIZED) for t in types):
        bad("length bounds on a type without a length")

    if f.schema is not None:
        _check_schema(f.schema, where)
    if f.item is not None:
        it = f.item
        if it.required or it.default is not _MISSING or it.requires or it.conflicts_with or it.required_if:
            bad("item schema cannot declare required/default/dependencies")
        _check_field(it, f"{where}[]")

    # A default is a value like any other: it must satisfy its own constraints.
    if f.default is not _MISSING and f.default is not None:
        d = f.default() if callable(f.default) else copy.deepcopy(f.default)
        problems: list[str] = []
        _check_value(d, f, where, problems)
        if problems:
            bad(f"default {d!r} is invalid ({'; '.join(problems)})")


def _check_schema(schema: dict[str, Field], path: str = "") -> None:
    prefix = f"{path}." if path else ""
    for key, f in schema.items():
        where = f"{prefix}{key}"
        _check_field(f, where)
        for dep in (*f.requires, *f.conflicts_with, *f.required_if):
            if dep not in schema:
                raise ValueError(f"schema error at {where!r}: dependency on unknown sibling {dep!r}")
        if key in f.requires or key in f.conflicts_with or key in f.required_if:
            raise ValueError(f"schema error at {where!r}: field depends on itself")
        if f.schema is not None:
            for rule in f.rules:
                for name in rule.fields:
                    if name not in f.schema:
                        raise ValueError(f"schema error at {where!r}: rule names unknown field {name!r}")
        elif f.rules:
            raise ValueError(f"schema error at {where!r}: rules require a nested schema")


# ------------------------------ Dependency checks ------------------------------

def _condition_holds(result: dict[str, Any], sibling: str, cond: Any) -> bool:
    """A condition on a sibling that is absent (or that makes the predicate blow up) is false."""
    if sibling not in result:
        return False
    actual = result[sibling]
    if callable(cond):
        try:
            return bool(cond(actual))
        except Exception:
            return False
    return _same(actual, cond)


def _describe(cond: dict[str, Any], prefix: str) -> str:
    return " and ".join(
        f"{prefix}{k} satisfies a condition" if callable(v) else f"{prefix}{k} is {v!r}"
        for k, v in cond.items()
    )


def _apply_dependencies(
    config: dict[str, Any],
    schema: dict[str, Field],
    result: dict[str, Any],
    rules: list[Rule],
    prefix: str,
    errors: list[str],
    errors_before: int,
) -> None:
    """Cross-field checks. "Set" means supplied by the user and not null."""

    def is_set(k: str) -> bool:
        return k in config and config[k] is not None

    reported_conflicts: set[frozenset[str]] = set()

    for key, f in schema.items():
        p = f"{prefix}{key}"
        if is_set(key):
            for dep in f.requires:
                if not is_set(dep):
                    errors.append(f"{p}: requires {prefix}{dep} to be set")
            for other in f.conflicts_with:
                pair = frozenset((key, other))
                if is_set(other) and pair not in reported_conflicts:
                    reported_conflicts.add(pair)
                    errors.append(f"{p}: cannot be set together with {prefix}{other}")
        elif f.required_if and all(_condition_holds(result, s, c) for s, c in f.required_if.items()):
            errors.append(f"{p}: required when {_describe(f.required_if, prefix)}")

    scope = prefix.rstrip(".") or "top level"
    for rule in rules:
        names = ", ".join(f"{prefix}{n}" for n in rule.fields)
        given = [n for n in rule.fields if is_set(n)]
        if rule.kind == "any_of" and not given:
            errors.append(f"{scope}: {rule.message or f'at least one of {names} is required'}")
        elif rule.kind == "one_of" and len(given) != 1:
            default = (f"exactly one of {names} is required" if not given
                       else f"only one of {names} may be set (got {', '.join(prefix + g for g in given)})")
            errors.append(f"{scope}: {rule.message or default}")
        elif rule.kind == "all_or_none" and given and len(given) != len(rule.fields):
            missing = ", ".join(f"{prefix}{n}" for n in rule.fields if n not in given)
            errors.append(f"{scope}: {rule.message or f'{names} must be set together (missing {missing})'}")
        elif rule.kind == "check":
            try:
                if rule.fn(result) is False:
                    errors.append(f"{scope}: {rule.message}")
            except Exception as exc:
                # If this scope already has errors, a predicate tripping over missing or
                # invalid data is a cascade of those errors; don't pile on a second one.
                if len(errors) == errors_before:
                    errors.append(f"{scope}: {rule.message} ({type(exc).__name__}: {exc})")


# ------------------------------ Core validation ------------------------------

def _check_value(value: Any, f: Field, path: str, errors: list[str]) -> Any:
    """Entry point for any value: handles explicit null, then full validation."""
    if value is None:
        if not f.nullable:
            errors.append(f"{path}: must not be null")
        return None
    return _validate_value(value, f, path, errors)


def _validate_value(value: Any, f: Field, path: str, errors: list[str]) -> Any:
    types = _types_of(f)

    if f.coerce and types:
        value, ok = _coerce(value, types, path, errors)
        if not ok:
            return value

    if types:
        if not _matches(value, types):
            errors.append(f"{path}: expected {_names(types)}, got {type(value).__name__}")
            return value
        if float in types and int not in types and isinstance(value, int) and not isinstance(value, bool):
            try:
                value = float(value)
            except OverflowError:
                errors.append(f"{path}: integer is too large to represent as float")
                return value

    if f.strip and isinstance(value, str):
        value = value.strip()

    # NaN compares False against everything, so it would sail through every bound.
    if isinstance(value, float) and not math.isfinite(value) and not f.allow_nonfinite:
        errors.append(f"{path}: must be a finite number, got {value!r}")
        return value

    if f.schema is not None and not isinstance(value, dict):
        errors.append(f"{path}: expected dict, got {type(value).__name__}")
        return value
    if f.item is not None and not isinstance(value, list):
        errors.append(f"{path}: expected list, got {type(value).__name__}")
        return value

    if f.choices is not None and not any(_same(value, c) for c in f.choices):
        errors.append(f"{path}: {value!r} not in allowed values {f.choices}")

    if _is_num(value):
        if f.min is not None and value < f.min:
            errors.append(f"{path}: {value} is below minimum {f.min}")
        if f.max is not None and value > f.max:
            errors.append(f"{path}: {value} is above maximum {f.max}")
        if f.gt is not None and not value > f.gt:
            errors.append(f"{path}: {value} must be greater than {f.gt}")
        if f.lt is not None and not value < f.lt:
            errors.append(f"{path}: {value} must be less than {f.lt}")

    if hasattr(value, "__len__"):
        if f.min_len is not None and len(value) < f.min_len:
            errors.append(f"{path}: length {len(value)} is below minimum {f.min_len}")
        if f.max_len is not None and len(value) > f.max_len:
            errors.append(f"{path}: length {len(value)} is above maximum {f.max_len}")

    if f.validator is not None:
        try:
            if f.validator(value) is False:
                errors.append(f"{path}: {f.message or 'failed custom validation'}")
        except Exception as exc:
            errors.append(f"{path}: {f.message or exc}")

    if f.schema is not None:
        value = _validate_dict(value, f.schema, path, errors, f.allow_extra, f.rules)
    elif f.item is not None:
        value = [_check_value(v, f.item, f"{path}[{i}]", errors) for i, v in enumerate(value)]

    return value


def _validate_dict(
    config: dict[str, Any],
    schema: dict[str, Field],
    path: str,
    errors: list[str],
    allow_extra: bool,
    rules: list[Rule] | None = None,
) -> dict[str, Any]:
    errors_before = len(errors)
    result: dict[str, Any] = {}
    prefix = f"{path}." if path else ""

    for key, f in schema.items():
        p = f"{prefix}{key}"
        if key in config:
            result[key] = _check_value(config[key], f, p, errors)
        elif f.default is not _MISSING:
            d = f.default
            result[key] = d() if callable(d) else copy.deepcopy(d)
        elif f.required:
            errors.append(f"{p}: required field is missing")
        elif f.schema is not None:
            # Optional section omitted: fill nested defaults only if that succeeds on its
            # own; unmet required children must not create errors for an unused section.
            scratch: list[str] = []
            nested = _validate_dict({}, f.schema, p, scratch, f.allow_extra, f.rules)
            if not scratch:
                result[key] = nested

    extras = sorted(set(config) - set(schema), key=str)
    if allow_extra:
        for k in extras:
            result[k] = copy.deepcopy(config[k])
    else:
        errors.extend(f"{prefix}{k}: unknown field" for k in extras)

    _apply_dependencies(config, schema, result, rules or [], prefix, errors, errors_before)
    return result


def validate(
    config: Any,
    schema: dict[str, Field],
    *,
    allow_extra: bool = False,
    rules: list[Rule] | None = None,
) -> dict[str, Any]:
    """Validate `config` against `schema`; return a new dict with defaults applied.

    Raises ConfigError listing all problems at once, and ValueError if the schema
    itself is inconsistent.
    """
    _check_schema(schema)
    for rule in rules or []:
        for name in rule.fields:
            if name not in schema:
                raise ValueError(f"schema error: top-level rule names unknown field {name!r}")
    if not isinstance(config, dict):
        raise ConfigError([f"top level: expected dict, got {type(config).__name__}"])
    errors: list[str] = []
    result = _validate_dict(config, schema, "", errors, allow_extra, rules)
    if errors:
        raise ConfigError(errors)
    return result


def load_config(
    path: str,
    schema: dict[str, Field],
    env_prefix: str = "",
    *,
    rules: list[Rule] | None = None,
    empty_env_is_unset: bool = True,
) -> dict[str, Any]:
    """Load JSON, overlay top-level env vars (PREFIX_KEY), then validate.

    The caller's schema is never mutated; env-overridden fields get a coercing copy.
    With `empty_env_is_unset`, `PREFIX_KEY=""` is ignored instead of overriding the file.
    """
    try:
        with open(path, encoding="utf-8-sig") as fh:      # tolerate a UTF-8 BOM
            raw = json.load(fh)
    except FileNotFoundError:
        raise ConfigError([f"config file not found: {path}"]) from None
    except UnicodeDecodeError:
        raise ConfigError([f"{path}: file is not valid UTF-8"]) from None
    except json.JSONDecodeError as exc:                    # includes empty files
        raise ConfigError([f"{path}: invalid JSON ({exc})"]) from None
    except OSError as exc:                                 # directory, permissions, ...
        raise ConfigError([f"{path}: cannot read file ({exc.strerror or exc})"]) from None
    if not isinstance(raw, dict):
        raise ConfigError([f"{path}: top level must be an object"])

    env_errors: list[str] = []
    effective = dict(schema)
    if env_prefix:
        for key, f in schema.items():
            name = f"{env_prefix}{key.upper()}"
            env_val = os.environ.get(name)
            if env_val is None or (empty_env_is_unset and env_val == ""):
                continue
            if f.schema is not None or f.item is not None or any(t in (dict, list) for t in _types_of(f)):
                try:
                    raw[key] = json.loads(env_val)
                except json.JSONDecodeError as exc:
                    env_errors.append(f"{name}: invalid JSON ({exc})")
            else:
                raw[key] = env_val
                effective[key] = dataclasses.replace(f, coerce=True)

    try:
        result = validate(raw, effective, rules=rules)
    except ConfigError as exc:
        raise ConfigError(env_errors + exc.errors) from None
    if env_errors:
        raise ConfigError(env_errors)
    return result


# ------------------------------- Example -------------------------------
if __name__ == "__main__":
    SCHEMA = {
        "app_name": Field(str, required=True, min_len=1, strip=True),
        "env": Field(str, default="dev", choices=["dev", "staging", "prod"]),
        "port": Field(int, default=8000, min=1, max=65535, coerce=True),   # inclusive: 1 and 65535 pass
        "ratio": Field(float, default=0.5, gt=0, max=1),                   # 0 fails, 1 passes
        "retries": Field(int, default=3, min=0, max=10),
        "timeout": Field((int, float), default=30, gt=0),
        # A predicate on a sibling that's absent is simply "not met", never a crash
        "workers": Field(int, min=1, required_if={"port": lambda p: p < 1024}),
        "allowed_hosts": Field(list, default=list, max_len=3, item=Field(str, min_len=1)),
        "database": Field(
            dict,
            required=True,
            schema={
                "url": Field(str, required=True, min_len=1),
                "pool_size": Field(int, default=5, min=1, max=100),
            },
        ),
        "cache": Field(dict, schema={"host": Field(str, required=True), "ttl": Field(int, default=60)}),
        "tags": Field(list, nullable=True, default=None, item=Field(str)),
    }

    print("--- exactly on the boundaries: all valid; omitted optional section is fine ---")
    edge = {"app_name": "  demo  ", "port": 65535, "ratio": 1, "retries": 0,
            "database": {"url": "sqlite:///a.db", "pool_size": 100}}
    print(validate(edge, SCHEMA))

    print("\n--- completely empty config: every missing field reported at once ---")
    try:
        validate({}, SCHEMA)
    except ConfigError as e:
        print(e)

    print("\n--- one step past each boundary, plus nasty values ---")
    bad = {
        "app_name": "   ",                          # blank after strip -> min_len
        "port": "1_000",                           # underscores are not a valid int string
        "ratio": 0,                                # exclusive lower bound
        "retries": 11,                             # above max
        "timeout": float("nan"),                   # NaN would pass every comparison
        "allowed_hosts": ["a", "b", "c", ""],      # too long, and an empty item
        "database": {"pool_size": 0},              # missing url, pool_size below min
        "cache": {},                               # present section: required child enforced
    }
    try:
        validate(bad, SCHEMA)
    except ConfigError as e:
        print(e)

    print("\n--- huge int for a float field, bool for a number ---")
    try:
        validate({"app_name": "x", "ratio": 10**400, "retries": True,
                  "database": {"url": "u"}}, SCHEMA)
    except ConfigError as e:
        print(e)

    print("\n--- contradictory schema fails fast ---")
    try:
        validate({}, {"n": Field(int, default=0, min=1)})
    except ValueError as e:
        print(e)