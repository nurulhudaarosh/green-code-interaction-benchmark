from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable

_MISSING = object()


class ConfigError(Exception):
    """Raised when validation fails; holds every error found, not just the first."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid configuration:\n  - " + "\n  - ".join(errors))


@dataclass
class Field:
    type: type | tuple[type, ...] | None = None
    required: bool = False
    default: Any = _MISSING
    choices: list[Any] | None = None
    min: float | None = None
    max: float | None = None
    min_len: int | None = None
    max_len: int | None = None
    validator: Callable[[Any], bool] | None = None   # return False or raise ValueError
    message: str | None = None                       # custom message for validator
    schema: dict[str, "Field"] | None = None         # nested dict schema
    item: "Field | None" = None                      # schema for list items
    coerce: bool = False                             # try type(value) before checking
    allow_extra: bool = False                        # nested dicts: permit unknown keys


def _validate_value(value: Any, f: Field, path: str, errors: list[str]) -> Any:
    # Coercion (e.g. "8080" -> 8080 from env vars)
    if f.coerce and f.type and not isinstance(value, f.type):
        target = f.type if isinstance(f.type, type) else f.type[0]
        try:
            if target is bool and isinstance(value, str):
                lowered = value.strip().lower()
                if lowered not in {"true", "false", "1", "0", "yes", "no"}:
                    raise ValueError
                value = lowered in {"true", "1", "yes"}
            else:
                value = target(value)
        except (ValueError, TypeError):
            errors.append(f"{path}: cannot convert {value!r} to {target.__name__}")
            return value

    # Type check (bool is an int subclass, so reject it for numeric fields)
    if f.type is not None:
        types = f.type if isinstance(f.type, tuple) else (f.type,)
        is_bool_misuse = isinstance(value, bool) and bool not in types
        if not isinstance(value, types) or is_bool_misuse:
            names = "/".join(t.__name__ for t in types)
            errors.append(f"{path}: expected {names}, got {type(value).__name__}")
            return value

    if f.choices is not None and value not in f.choices:
        errors.append(f"{path}: {value!r} not in allowed values {f.choices}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
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

    if f.schema is not None and isinstance(value, dict):
        value = validate(value, f.schema, _path=path, _errors=errors, allow_extra=f.allow_extra)

    if f.item is not None and isinstance(value, list):
        value = [
            _validate_value(v, f.item, f"{path}[{i}]", errors) for i, v in enumerate(value)
        ]

    return value


def validate(
    config: dict[str, Any],
    schema: dict[str, Field],
    *,
    allow_extra: bool = False,
    _path: str = "",
    _errors: list[str] | None = None,
) -> dict[str, Any]:
    """Validate `config` against `schema`; return a new dict with defaults applied.

    Raises ConfigError listing all problems at once.
    """
    top_level = _errors is None
    errors: list[str] = [] if _errors is None else _errors
    result: dict[str, Any] = {}
    prefix = f"{_path}." if _path else ""

    for key, f in schema.items():
        path = f"{prefix}{key}"
        if key in config and config[key] is not None:
            result[key] = _validate_value(config[key], f, path, errors)
        elif f.required and f.default is _MISSING:
            errors.append(f"{path}: required field is missing")
        elif f.default is not _MISSING:
            result[key] = f.default() if callable(f.default) else f.default
        elif f.schema is not None:
            # Apply nested defaults even when the section is omitted
            result[key] = validate({}, f.schema, _path=path, _errors=errors)

    extras = set(config) - set(schema)
    if extras and not allow_extra:
        for key in sorted(extras):
            errors.append(f"{prefix}{key}: unknown field")
    elif extras:
        result.update({k: config[k] for k in extras})

    if top_level and errors:
        raise ConfigError(errors)
    return result


def load_config(path: str, schema: dict[str, Field], env_prefix: str = "") -> dict[str, Any]:
    """Load JSON, overlay top-level env vars (PREFIX_KEY), then validate."""
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        raise ConfigError([f"config file not found: {path}"])
    except json.JSONDecodeError as exc:
        raise ConfigError([f"{path}: invalid JSON ({exc})"])
    if not isinstance(raw, dict):
        raise ConfigError([f"{path}: top level must be an object"])

    if env_prefix:
        for key, f in schema.items():
            env_val = os.environ.get(f"{env_prefix}{key.upper()}")
            if env_val is not None:
                raw[key] = env_val
                f.coerce = True  # env vars are always strings

    return validate(raw, schema)


# ------------------------------- Example -------------------------------
if __name__ == "__main__":
    SCHEMA = {
        "app_name": Field(str, required=True, min_len=1),
        "env": Field(str, default="dev", choices=["dev", "staging", "prod"]),
        "port": Field(int, default=8000, min=1, max=65535, coerce=True),
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
    }

    good = {"app_name": "demo", "port": "9000", "database": {"url": "sqlite:///app.db"}}
    print(validate(good, SCHEMA))

    bad = {
        "env": "qa",
        "port": 99999,
        "debug": "maybe",
        "allowed_hosts": ["ok", ""],
        "database": {"url": "mysql://x", "pool_size": 0},
        "extra": 1,
    }
    try:
        validate(bad, SCHEMA)
    except ConfigError as e:
        print(e)