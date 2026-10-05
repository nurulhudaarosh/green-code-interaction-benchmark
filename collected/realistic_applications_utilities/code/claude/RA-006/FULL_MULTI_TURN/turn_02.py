from __future__ import annotations

import copy
import dataclasses
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Callable

_MISSING = object()


class ConfigError(Exception):
    """Raised when validation fails; holds every error found, not just the first."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid configuration:\n  - " + "\n  - ".join(errors))


@dataclass
class Field:
    type: Any = None                      # a type or tuple of types
    required: bool = False
    default: Any = _MISSING               # value, or zero-arg callable (called fresh each time)
    nullable: bool = False                # explicit null is allowed
    choices: list[Any] | None = None
    min: float | None = None
    max: float | None = None
    min_len: int | None = None
    max_len: int | None = None
    validator: Callable[[Any], bool] | None = None
    message: str | None = None
    schema: dict[str, "Field"] | None = None   # nested dict schema (value must be a dict)
    item: "Field | None" = None                # list item schema (value must be a list)
    coerce: bool = False
    allow_extra: bool = False


def _types_of(f: Field) -> tuple[type, ...]:
    if f.type is None:
        return ()
    return f.type if isinstance(f.type, tuple) else (f.type,)


def _names(types: tuple[type, ...]) -> str:
    return "/".join(t.__name__ for t in types)


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
        if isinstance(value, str) and value.strip().lower() in {"true", "false", "1", "0", "yes", "no"}:
            return value.strip().lower() in {"true", "1", "yes"}
        raise ValueError
    if target is int:
        if isinstance(value, str):
            return int(value.strip())
        if isinstance(value, float) and value.is_integer():
            return int(value)
        raise ValueError
    if target is float:
        if isinstance(value, (str, int)):
            result = float(value)
            if not math.isfinite(result):
                raise ValueError
            return result
        raise ValueError
    if target is str:
        if _is_num(value):
            return str(value)
        raise ValueError
    raise ValueError  # never coerce into list/dict/etc. (list("abc") is not a conversion)


def _coerce(value: Any, types: tuple[type, ...], path: str, errors: list[str]) -> tuple[Any, bool]:
    if _matches(value, types):
        return value, True
    if isinstance(value, (str, int, float)):  # only scalars are coercible, bool included
        for target in types:
            try:
                return _coerce_one(value, target), True
            except (ValueError, TypeError):
                continue
    errors.append(f"{path}: cannot convert {value!r} to {_names(types)}")
    return value, False


def _check(value: Any, f: Field, path: str, errors: list[str]) -> Any:
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
        if float in types and int not in types and _is_num(value):
            value = float(value)  # normalise int -> float

    # Structural requirements hold even when no explicit type was given
    if f.schema is not None and not isinstance(value, dict):
        errors.append(f"{path}: expected dict, got {type(value).__name__}")
        return value
    if f.item is not None and not isinstance(value, list):
        errors.append(f"{path}: expected list, got {type(value).__name__}")
        return value

    if f.choices is not None and value not in f.choices:
        errors.append(f"{path}: {value!r} not in allowed values {f.choices}")

    if _is_num(value):
        if f.min is not None and value < f.min:
            errors.append(f"{path}: {value} is below minimum {f.min}")
        if f.max is not None and value > f.max:
            errors.append(f"{path}: {value} is above maximum {f.max}")

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
        value = _validate_dict(value, f.schema, path, errors, f.allow_extra)
    elif f.item is not None:
        value = [_check(v, f.item, f"{path}[{i}]", errors) for i, v in enumerate(value)]

    return value


def _validate_dict(
    config: dict[str, Any],
    schema: dict[str, Field],
    path: str,
    errors: list[str],
    allow_extra: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    prefix = f"{path}." if path else ""

    for key, f in schema.items():
        p = f"{prefix}{key}"
        if key in config:
            result[key] = _check(config[key], f, p, errors)
        elif f.default is not _MISSING:
            d = f.default
            result[key] = d() if callable(d) else copy.deepcopy(d)
        elif f.required:
            errors.append(f"{p}: required field is missing")
        elif f.schema is not None:
            # Optional section omitted: fill nested defaults, but only if that
            # succeeds on its own. Unmet required children must not create
            # errors for a section nobody asked for.
            scratch: list[str] = []
            nested = _validate_dict({}, f.schema, p, scratch, f.allow_extra)
            if not scratch:
                result[key] = nested

    extras = sorted(set(config) - set(schema), key=str)
    if allow_extra:
        for k in extras:
            result[k] = copy.deepcopy(config[k])
    else:
        errors.extend(f"{prefix}{k}: unknown field" for k in extras)

    return result


def validate(config: Any, schema: dict[str, Field], *, allow_extra: bool = False) -> dict[str, Any]:
    """Validate `config` against `schema`; return a new dict with defaults applied.

    Raises ConfigError listing all problems at once.
    """
    errors: list[str] = []
    if not isinstance(config, dict):
        raise ConfigError([f"top level: expected dict, got {type(config).__name__}"])
    result = _validate_dict(config, schema, "", errors, allow_extra)
    if errors:
        raise ConfigError(errors)
    return result


def load_config(path: str, schema: dict[str, Field], env_prefix: str = "") -> dict[str, Any]:
    """Load JSON, overlay top-level env vars (PREFIX_KEY), then validate.

    The caller's schema is never mutated; env-overridden fields get a coercing copy.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        raise ConfigError([f"config file not found: {path}"]) from None
    except json.JSONDecodeError as exc:
        raise ConfigError([f"{path}: invalid JSON ({exc})"]) from None
    if not isinstance(raw, dict):
        raise ConfigError([f"{path}: top level must be an object"])

    env_errors: list[str] = []
    effective = dict(schema)
    if env_prefix:
        for key, f in schema.items():
            env_val = os.environ.get(f"{env_prefix}{key.upper()}")
            if env_val is None:
                continue
            if f.schema is not None or f.item is not None or any(t in (dict, list) for t in _types_of(f)):
                try:
                    raw[key] = json.loads(env_val)  # structured values arrive as JSON
                except json.JSONDecodeError as exc:
                    env_errors.append(f"{env_prefix}{key.upper()}: invalid JSON ({exc})")
            else:
                raw[key] = env_val
                effective[key] = dataclasses.replace(f, coerce=True)

    try:
        return validate(raw, effective)
    except ConfigError as exc:
        raise ConfigError(env_errors + exc.errors) from None
    finally:
        if env_errors:
            pass  # (errors already merged above when validation fails)


# ------------------------------- Example -------------------------------
if __name__ == "__main__":
    SCHEMA = {
        "app_name": Field(str, required=True, min_len=1),
        "env": Field(str, default="dev", choices=["dev", "staging", "prod"]),
        "port": Field(int, default=8000, min=1, max=65535, coerce=True),
        "ratio": Field(float, default=0.5, min=0, max=1),
        "debug": Field(bool, default=False, coerce=True),
        "allowed_hosts": Field(list, default=list, item=Field(str, min_len=1)),
        "database": Field(
            dict,
            required=True,
            schema={
                "url": Field(
                    str,
                    required=True,
                    validator=lambda v: v.startswith(("postgresql://", "sqlite:///")),
                    message="must start with postgresql:// or sqlite:///",
                ),
                "pool_size": Field(int, default=5, min=1, max=100),
            },
        ),
        # Optional section with a required child: omitting it must NOT be an error
        "cache": Field(dict, schema={"host": Field(str, required=True), "ttl": Field(int, default=60)}),
        "tags": Field(list, nullable=True, default=None, item=Field(str)),
    }

    good = {"app_name": "demo", "port": "9000", "ratio": 1, "database": {"url": "sqlite:///app.db"}}
    print(validate(good, SCHEMA))  # ratio -> 1.0, no cache error, tags None

    bad = {
        "app_name": None,                      # null for non-nullable
        "env": "qa",
        "port": 3.7,                           # lossy float -> int is rejected
        "debug": "maybe",
        "ratio": True,                         # bool is not a float
        "allowed_hosts": "localhost",          # str where list expected (not split into chars)
        "database": "sqlite:///x",             # str where nested dict expected
        "cache": {"ttl": "x"},                 # present section: required child enforced
        "extra": 1,
    }
    try:
        validate(bad, SCHEMA)
    except ConfigError as e:
        print(e)