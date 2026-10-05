#!/usr/bin/env python3
"""
Configuration Validation System — final version.

Two fixes applied:
  FIX 1  Nested-path resolution now handles:
           - flat keys containing dots   {"server.port": 80}
           - deep nesting                {"server": {"port": 80}}
           - list/tuple indexing         {"servers": [{"port": 80}]}
           - distinguishes MISSING from a present falsy value (0, False, "", [])
  FIX 2  Boolean type handling in TypeRule / Range / Port / Choices now:
           - rejects bool where int/float/str is expected (unless allow_bool=True)
           - rejects int where bool is expected (unless allow_int=True, only 0/1)
           - Port and Range no longer treat True/False as 1/0
"""

from __future__ import annotations

import ipaddress
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, Union
from urllib.parse import urlparse


# ============================================================
# FIX 1 — sentinel + robust path resolver
# ============================================================
MISSING = object()


def resolve_path(config: Any, dotted: str) -> Any:
    """
    Resolve a dotted path against a nested (or flat) config structure.

    Supports, at every level:
      * literal key that contains dots  -> {"server.port": 80}
      * plain nested dict lookup        -> {"server": {"port": 80}}
      * list/tuple index                -> {"servers": [{"port": 80}]}
    Returns MISSING when the path is absent. Present-but-falsy values
    (0, False, "", []) are returned as-is, never coerced to MISSING.
    """
    if not dotted:
        return MISSING

    # Top-level literal key wins — so a config written as {"server.port": 80}
    # is honoured even without any nesting.
    if isinstance(config, dict) and dotted in config:
        return config[dotted]

    cur: Any = config
    parts = dotted.split(".")
    i = 0
    while i < len(parts):
        if isinstance(cur, dict):
            # Greedy: try the longest remaining literal key first, so that
            # mid-path flat keys (e.g. "a.b" inside {"a.b": {"c": 1}}) work.
            matched = False
            for j in range(len(parts), i, -1):
                candidate = ".".join(parts[i:j])
                if candidate in cur:
                    cur = cur[candidate]
                    i = j
                    matched = True
                    break
            if matched:
                continue
            part = parts[i]
            if part in cur:
                cur = cur[part]
                i += 1
                continue
            return MISSING

        if isinstance(cur, (list, tuple)):
            part = parts[i]
            if not part.lstrip("-").isdigit():
                return MISSING
            idx = int(part)
            if -len(cur) <= idx < len(cur):
                cur = cur[idx]
                i += 1
                continue
            return MISSING

        # scalar reached but path continues
        return MISSING

    return cur


def has_path(config: Any, dotted: str) -> bool:
    return resolve_path(config, dotted) is not MISSING


# ============================================================
# Result types
# ============================================================
class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    path: str
    message: str
    severity: Severity = Severity.ERROR
    rule: str = ""
    value: Any = None

    def __str__(self) -> str:
        shown = "<missing>" if self.value is MISSING else repr(self.value)
        return f"[{self.severity.value.upper()}] {self.path}: {self.message} (rule={self.rule}, value={shown})"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == Severity.ERROR for i in self.issues)

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def report(self) -> str:
        if not self.issues:
            return "Configuration is valid."
        head = f"Validation finished: {len(self.errors())} error(s), {len(self.warnings())} warning(s)"
        return "\n".join([head] + [str(i) for i in self.issues])


# ============================================================
# Rule engine
# ============================================================
class Rule:
    name = "rule"

    def check(self, path: str, value: Any, config: dict) -> Optional[ValidationIssue]:
        raise NotImplementedError


class Required(Rule):
    name = "required"

    def check(self, path, value, config):
        # MISSING means the key is absent; None or "" means it's set to nothing.
        if value is MISSING or value is None or value == "":
            return ValidationIssue(path, "is required", rule=self.name,
                                   value=None if value is MISSING else value)
        return None


class TypeRule(Rule):
    """
    FIX 2 — correct bool-vs-int semantics.

    Defaults:
      expected=int/float  -> bool is rejected (allow_bool=True to permit)
      expected=bool       -> only bool accepted (allow_int=True permits 0/1)
      expected=str        -> only str accepted, bool rejected automatically
    """
    name = "type"

    def __init__(self, expected: Union[type, tuple], *,
                 allow_bool: bool = False, allow_int: bool = False):
        self.allow_bool = allow_bool
        self.allow_int = allow_int
        self.expected: tuple = (expected,) if isinstance(expected, type) else tuple(expected)

    def _ok(self, value: Any) -> bool:
        # --- bool branch ---
        if isinstance(value, bool):
            if bool in self.expected:
                return True
            if self.allow_bool and (int in self.expected or float in self.expected):
                return True
            return False

        # --- non-bool int branch ---
        if isinstance(value, int) and not isinstance(value, bool):
            if int in self.expected:
                return True
            if float in self.expected:
                return True  # int is a valid float
            if bool in self.expected and self.allow_int and value in (0, 1):
                return True
            return False

        # --- everything else ---
        return isinstance(value, self.expected)

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        if self._ok(value):
            return None
        names = "/".join(t.__name__ for t in self.expected)
        return ValidationIssue(path,
                               f"must be {names}, got {type(value).__name__}",
                               rule=self.name, value=value)


class Range(Rule):
    name = "range"

    def __init__(self, min_val=None, max_val=None, inclusive=True):
        self.min_val, self.max_val, self.inclusive = min_val, max_val, inclusive

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        # FIX 2: never coerce True/False to 1/0 for range comparisons.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if self.min_val is not None:
            bad = value < self.min_val if self.inclusive else value <= self.min_val
            if bad:
                op = ">=" if self.inclusive else ">"
                return ValidationIssue(path, f"must be {op} {self.min_val}, got {value}",
                                       rule=self.name, value=value)
        if self.max_val is not None:
            bad = value > self.max_val if self.inclusive else value >= self.max_val
            if bad:
                op = "<=" if self.inclusive else "<"
                return ValidationIssue(path, f"must be {op} {self.max_val}, got {value}",
                                       rule=self.name, value=value)
        return None


class Length(Rule):
    name = "length"

    def __init__(self, min_len=None, max_len=None, exact=None):
        self.min_len, self.max_len, self.exact = min_len, max_len, exact

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        try:
            n = len(value)
        except TypeError:
            return None
        if self.exact is not None and n != self.exact:
            return ValidationIssue(path, f"length must be exactly {self.exact}, got {n}",
                                   rule=self.name, value=value)
        if self.min_len is not None and n < self.min_len:
            return ValidationIssue(path, f"length must be >= {self.min_len}, got {n}",
                                   rule=self.name, value=value)
        if self.max_len is not None and n > self.max_len:
            return ValidationIssue(path, f"length must be <= {self.max_len}, got {n}",
                                   rule=self.name, value=value)
        return None


class Pattern(Rule):
    name = "pattern"

    def __init__(self, regex: str, flags: int = 0):
        self.regex = re.compile(regex, flags)

    def check(self, path, value, config):
        if value is MISSING or value is None or not isinstance(value, str):
            return None
        if not self.regex.fullmatch(value):
            return ValidationIssue(path, f"must match pattern {self.regex.pattern!r}",
                                   rule=self.name, value=value)
        return None


class Choices(Rule):
    name = "choices"

    def __init__(self, options: List[Any], case_sensitive: bool = True):
        self.options = options
        self.case_sensitive = case_sensitive

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        opts, v = self.options, value
        if not self.case_sensitive and isinstance(value, str):
            opts = [o.lower() if isinstance(o, str) else o for o in self.options]
            v = value.lower()
        # FIX 2: strict identity check for booleans so True != 1 in choice lists.
        for o in opts:
            if isinstance(o, bool) or isinstance(v, bool):
                if o is v:
                    return None
            elif o == v:
                return None
        return ValidationIssue(path, f"must be one of {self.options}, got {value!r}",
                               rule=self.name, value=value)


class Custom(Rule):
    name = "custom"

    def __init__(self, func: Callable[[Any, dict], bool], message: str = "failed custom check"):
        self.func, self.message = func, message

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        try:
            if not self.func(value, config):
                return ValidationIssue(path, self.message, rule=self.name, value=value)
        except Exception as e:
            return ValidationIssue(path, f"custom check raised {e!r}",
                                   rule=self.name, value=value)
        return None


class URL(Rule):
    name = "url"

    def __init__(self, schemes: Optional[List[str]] = None, require_host: bool = True):
        self.schemes = schemes or ["http", "https"]
        self.require_host = require_host

    def check(self, path, value, config):
        if value is MISSING or value is None or not isinstance(value, str):
            return None
        try:
            parsed = urlparse(value)
        except Exception as e:
            return ValidationIssue(path, f"invalid URL: {e}", rule=self.name, value=value)
        if parsed.scheme not in self.schemes:
            return ValidationIssue(path, f"URL scheme must be one of {self.schemes}",
                                   rule=self.name, value=value)
        if self.require_host and not parsed.hostname:
            return ValidationIssue(path, "URL must have a host",
                                   rule=self.name, value=value)
        return None


class Email(Rule):
    name = "email"
    _re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def check(self, path, value, config):
        if value is MISSING or value is None or not isinstance(value, str):
            return None
        if not self._re.match(value):
            return ValidationIssue(path, "must be a valid email",
                                   rule=self.name, value=value)
        return None


class Hostname(Rule):
    name = "hostname"
    _re = re.compile(r"^(?=.{1,253}$)([a-zA-Z0-9](-?[a-zA-Z0-9])*)(\.[a-zA-Z0-9](-?[a-zA-Z0-9])*)*$")

    def check(self, path, value, config):
        if value is MISSING or value is None or not isinstance(value, str):
            return None
        if not self._re.match(value):
            return ValidationIssue(path, "must be a valid hostname",
                                   rule=self.name, value=value)
        return None


class IPAddress(Rule):
    name = "ip"

    def __init__(self, version: Optional[int] = None):
        self.version = version

    def check(self, path, value, config):
        if value is MISSING or value is None or not isinstance(value, str):
            return None
        try:
            ip = ipaddress.ip_address(value)
        except ValueError:
            return ValidationIssue(path, "must be a valid IP address",
                                   rule=self.name, value=value)
        if self.version and ip.version != self.version:
            return ValidationIssue(path, f"must be IPv{self.version}",
                                   rule=self.name, value=value)
        return None


class Port(Rule):
    name = "port"

    def check(self, path, value, config):
        if value is MISSING or value is None:
            return None
        # FIX 2: True is not a port.
        if isinstance(value, bool) or not isinstance(value, int):
            return ValidationIssue(path, "port must be an integer",
                                   rule=self.name, value=value)
        if not (1 <= value <= 65535):
            return ValidationIssue(path, "port must be between 1 and 65535",
                                   rule=self.name, value=value)
        return None


class DependsOn(Rule):
    name = "depends_on"

    def __init__(self, other_path: str):
        self.other_path = other_path

    def check(self, path, value, config):
        if value is MISSING or value in (None, "", [], {}, 0, False):
            return None
        other = resolve_path(config, self.other_path)
        if other is MISSING or other in (None, "", [], {}):
            return ValidationIssue(path, f"requires '{self.other_path}' to be set",
                                   rule=self.name, value=value)
        return None


class MutuallyExclusive(Rule):
    name = "mutually_exclusive"

    def __init__(self, others: List[str]):
        self.others = others

    def check(self, path, value, config):
        if value is MISSING or value in (None, "", [], {}):
            return None
        for other in self.others:
            ov = resolve_path(config, other)
            if ov is not MISSING and ov not in (None, "", [], {}):
                return ValidationIssue(path, f"mutually exclusive with '{other}'",
                                       rule=self.name, value=value)
        return None


class NoExtraKeys(Rule):
    name = "no_extra_keys"

    def __init__(self, allowed: List[str]):
        self.allowed = set(allowed)

    def check(self, path, value, config):
        if not isinstance(value, dict):
            return None
        extras = set(value) - self.allowed
        if extras:
            return ValidationIssue(path, f"unexpected keys: {sorted(extras)}",
                                   rule=self.name, value=sorted(extras))
        return None


# ============================================================
# Schema
# ============================================================
@dataclass
class FieldSchema:
    path: str
    rules: List[Rule] = field(default_factory=list)
    optional: bool = True

    def validate(self, config: dict, result: ValidationResult) -> Any:
        value = resolve_path(config, self.path)
        present = value is not MISSING
        for rule in self.rules:
            if isinstance(rule, Required):
                if not present and self.optional:
                    continue
            elif not present:
                # Non-required rules don't fire on absent fields.
                continue
            issue = rule.check(self.path, value, config)
            if issue:
                result.add(issue)
        return value


@dataclass
class ConfigSchema:
    fields: List[FieldSchema] = field(default_factory=list)

    def field(self, path: str, *rules: Rule, optional: bool = True) -> "ConfigSchema":
        self.fields.append(FieldSchema(path=path, rules=list(rules), optional=optional))
        return self

    def validate(self, config: dict) -> ValidationResult:
        result = ValidationResult()
        for f in self.fields:
            f.validate(config, result)
        return result


# ============================================================
# Example schema
# ============================================================
def build_app_schema() -> ConfigSchema:
    s = ConfigSchema()

    s.field("app.name", Required(), TypeRule(str), Length(min_len=1, max_len=64),
            optional=False)
    s.field("app.env", Required(), Choices(["dev", "staging", "prod"]),
            optional=False)
    s.field("app.debug", TypeRule(bool))
    s.field("app.retries", TypeRule(int))                    # bool rejected
    s.field("app.version", Pattern(r"\d+\.\d+\.\d+"))

    s.field("server.host", TypeRule(str), Hostname())
    s.field("server.port", Required(), Port(), optional=False)
    s.field("server.workers", TypeRule(int), Range(min_val=1, max_val=128))
    s.field("server.timeout", TypeRule((int, float)), Range(min_val=0.1, max_val=300))
    s.field("server.protocol", Choices(["http", "https"], case_sensitive=False))
    s.field("server.keepalive", TypeRule(int, allow_bool=True), Range(min_val=0, max_val=1))

    s.field("database.url", Required(), TypeRule(str),
            URL(schemes=["postgres", "mysql", "sqlite"]), optional=False)
    s.field("database.pool_size", TypeRule(int), Range(min_val=1, max_val=100))
    s.field("database.ssl", TypeRule(bool))

    s.field("cache.enabled", TypeRule(bool))
    s.field("cache.host", DependsOn("cache.enabled"), IPAddress(version=4))
    s.field("cache.port", DependsOn("cache.enabled"), Port())

    s.field("auth.mode", Choices(["none", "basic", "jwt", "oauth"]))
    s.field("auth.secret", DependsOn("auth.mode"), Length(min_len=16))
    s.field("auth.basic_user", MutuallyExclusive(["auth.jwt_token"]))
    s.field("auth.jwt_token", MutuallyExclusive(["auth.basic_user"]))

    s.field("notifications.email", Email())
    s.field("notifications.webhook", URL(schemes=["https"]))

    def no_privileged_port(v, cfg):
        if isinstance(v, int) and not isinstance(v, bool) and v < 1024:
            app = cfg.get("app", {}) if isinstance(cfg.get("app"), dict) else {}
            return app.get("allow_privileged_ports", False)
        return True

    s.field("server.port",
            Custom(no_privileged_port,
                   "port < 1024 requires app.allow_privileged_ports=true"))

    s.field("app", NoExtraKeys(["name", "env", "debug", "retries", "version",
                                "allow_privileged_ports"]))
    return s


# ============================================================
# Env-override loader
# ============================================================
def _coerce(v: str) -> Any:
    try:
        return json.loads(v)
    except Exception:
        return v


def set_nested(cfg: dict, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = cfg
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def load_config(path: Optional[str] = None, env_prefix: str = "APP_") -> dict:
    cfg: dict = {}
    if path and Path(path).exists():
        with open(path) as f:
            cfg = json.load(f)
    for key, val in os.environ.items():
        if not key.startswith(env_prefix):
            continue
        dotted = key[len(env_prefix):].lower().replace("__", ".")
        set_nested(cfg, dotted, _coerce(val))
    return cfg


# ============================================================
# Regression tests for FIX 1 and FIX 2
# ============================================================
def test_path_resolution():
    assert resolve_path({"server.port": 80}, "server.port") == 80
    assert resolve_path({"server": {"port": 80}}, "server.port") == 80
    assert resolve_path({"servers": [{"host": "a"}, {"host": "b"}]},
                        "servers.0.host") == "a"
    assert resolve_path({"servers": [{"host": "a"}, {"host": "b"}]},
                        "servers.-1.host") == "b"
    assert resolve_path({"a": {"b": {"c": 0}}}, "a.b.c") == 0
    assert resolve_path({"a": {"b": {"c": False}}}, "a.b.c") is False
    assert resolve_path({"a": {"b": {"c": None}}}, "a.b.c") is None
    assert resolve_path({"a": {"b": {"c": ""}}}, "a.b.c") == ""
    assert resolve_path({"server": {}}, "server.port") is MISSING
    assert resolve_path({"a.b": {"c.d": 1}}, "a.b.c.d") == 1
    assert has_path({"x": 0}, "x") is True
    assert has_path({"x": 0}, "y") is False


def test_bool_handling():
    # int rejects bool by default
    assert TypeRule(int).check("x", True, {}) is not None
    assert TypeRule(int).check("x", 1, {}) is None

    # float rejects bool, accepts int
    assert TypeRule(float).check("x", False, {}) is not None
    assert TypeRule(float).check("x", 3, {}) is None
    assert TypeRule(float).check("x", 3.5, {}) is None

    # bool rejects plain ints unless allow_int
    assert TypeRule(bool).check("x", 1, {}) is not None
    assert TypeRule(bool).check("x", True, {}) is None
    assert TypeRule(bool, allow_int=True).check("x", 1, {}) is None
    assert TypeRule(bool, allow_int=True).check("x", 2, {}) is not None

    # int accepts bool when allow_bool=True
    assert TypeRule(int, allow_bool=True).check("x", True, {}) is None

    # Port rejects bool
    assert Port().check("x", True, {}) is not None
    assert Port().check("x", 8080, {}) is None

    # Range ignores bools instead of comparing them as 0/1
    assert Range(min_val=2).check("x", True, {}) is None

    # Choices distinguishes True from 1
    assert Choices([1]).check("x", True, {}) is not None
    assert Choices([True]).check("x", 1, {}) is not None
    assert Choices([True]).check("x", True, {}) is None


# ============================================================
# Demo
# ============================================================
def main():
    test_path_resolution()
    test_bool_handling()
    print("Regression tests passed.")
    print()

    bad = {
        "app": {"name": "", "env": "development", "debug": "yes",
                "retries": True,                 # bool for int -> now rejected
                "version": "1.0", "unknown_key": 42},
        "server": {"host": "not a host!", "port": 80, "workers": 500,
                   "timeout": 0.01, "protocol": "FTP",
                   "keepalive": True},           # bool allowed by declaration
        "database": {"pool_size": 0, "ssl": "maybe"},   # url missing
        "cache": {"enabled": True, "host": "999.1.1.1", "port": 70000},
        "auth": {"mode": "jwt", "secret": "short",
                 "basic_user": "admin", "jwt_token": "tok"},
        "notifications": {"email": "bad-email", "webhook": "ftp://example.com"},
    }
    print("=== BAD CONFIG ===")
    print(build_app_schema().validate(bad).report())
    print()

    # Demonstrate FIX 1: flat keys work too.
    flat_config = {
        "app.name": "flat-app",
        "app.env": "dev",
        "server.host": "localhost",
        "server.port": 8080,
        "database.url": "sqlite:///:memory:",
    }
    print("=== FLAT-KEY CONFIG (FIX 1) ===")
    print(build_app_schema().validate(flat_config).report())
    print()

    good = {
        "app": {"name": "myapp", "env": "prod", "debug": False,
                "retries": 3, "version": "1.2.3"},
        "server": {"host": "api.example.com", "port": 8443, "workers": 4,
                   "timeout": 30, "protocol": "https", "keepalive": True},
        "database": {"url": "postgres://db:5432/app", "pool_size": 10, "ssl": True},
        "cache": {"enabled": True, "host": "10.0.0.5", "port": 6379},
        "auth": {"mode": "jwt", "secret": "s3cr3t-key-1234567890"},
        "notifications": {"email": "ops@example.com",
                          "webhook": "https://hooks.example.com/x"},
    }
    print("=== GOOD CONFIG ===")
    print(build_app_schema().validate(good).report())


if __name__ == "__main__":
    main()