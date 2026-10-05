from typing import Any, Dict, List, Tuple


_MISSING = object()


def get_nested_value(config: Any, path: str) -> Tuple[Any, bool]:
    """Safely retrieve a nested value using dot notation."""
    if not isinstance(config, dict) or not isinstance(path, str):
        return _MISSING, False

    path = path.strip()
    if not path:
        return _MISSING, False

    current = config

    for part in path.split("."):
        part = part.strip()

        if not part or not isinstance(current, dict) or part not in current:
            return _MISSING, False

        current = current[part]

    return current, True


def matches_type(value: Any, expected_type: str) -> bool:
    """Strict type validation with correct boolean handling."""
    if not isinstance(expected_type, str):
        return False

    type_name = expected_type.strip().lower()

    if type_name in {"string", "str"}:
        return isinstance(value, str)

    if type_name in {"int", "integer"}:
        return isinstance(value, int) and not isinstance(value, bool)

    if type_name == "float":
        return isinstance(value, float)

    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    if type_name in {"bool", "boolean"}:
        return isinstance(value, bool)

    if type_name == "list":
        return isinstance(value, list)

    if type_name in {"dict", "object"}:
        return isinstance(value, dict)

    return False


def compare_boundary(
    value: Any,
    boundary: Any,
    operator: str
) -> bool:
    """Safely compare a value with a boundary."""
    try:
        if operator == "min":
            return value >= boundary
        if operator == "max":
            return value <= boundary
    except (TypeError, ValueError):
        return False

    return False


def validate_rule(
    config: Dict[str, Any],
    rule: Dict[str, Any]
) -> Tuple[bool, str]:
    """Validate a single field rule."""
    if not isinstance(rule, dict):
        return False, "Rule must be a dictionary."

    path = rule.get("path")

    if not isinstance(path, str) or not path.strip():
        return False, "Rule path must be a non-empty string."

    value, exists = get_nested_value(config, path)

    required = rule.get("required", False)

    if not isinstance(required, bool):
        return False, f"Invalid required setting for '{path}'."

    # Missing field handling.
    if not exists:
        if required:
            return False, f"Required field '{path}' is missing."

        # Optional missing fields are valid.
        return True, ""

    # If explicitly present as None, required fields still fail.
    if value is None:
        if required:
            return False, f"Required field '{path}' cannot be None."

        # Optional nullable fields are valid unless other constraints
        # explicitly require a type/value.
        if "type" not in rule and "min" not in rule and "max" not in rule:
            return True, ""

    # Type validation.
    if "type" in rule:
        expected_type = rule["type"]

        if not matches_type(value, expected_type):
            return (
                False,
                f"Field '{path}' has invalid type. "
                f"Expected {expected_type}."
            )

    # Inclusive minimum boundary.
    if "min" in rule:
        minimum = rule["min"]

        if not compare_boundary(value, minimum, "min"):
            return (
                False,
                f"Field '{path}' must be greater than or equal to {minimum}."
            )

    # Inclusive maximum boundary.
    if "max" in rule:
        maximum = rule["max"]

        if not compare_boundary(value, maximum, "max"):
            return (
                False,
                f"Field '{path}' must be less than or equal to {maximum}."
            )

    # Allowed values.
    if "allowed" in rule:
        allowed = rule["allowed"]

        if not isinstance(allowed, (list, tuple, set)):
            return False, f"'allowed' for '{path}' must be a collection."

        if value not in allowed:
            return False, f"Field '{path}' contains a disallowed value."

    return True, ""


def validate_dependency(
    config: Dict[str, Any],
    dependency: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate a cross-field dependency.

    Example:
        {
            "when": {"path": "server.enabled", "equals": True},
            "requires": ["server.host", "server.port"]
        }
    """
    if not isinstance(dependency, dict):
        return False, "Dependency must be a dictionary."

    when = dependency.get("when")
    requires = dependency.get("requires")

    if not isinstance(when, dict):
        return False, "'when' must be a dictionary."

    if not isinstance(requires, list):
        return False, "'requires' must be a list."

    condition_path = when.get("path")

    if not isinstance(condition_path, str) or not condition_path.strip():
        return False, "Dependency condition path must be non-empty."

    condition_value, condition_exists = get_nested_value(
        config, condition_path
    )

    # If the condition itself is missing, the dependency is not activated.
    if not condition_exists:
        return True, ""

    matched = False

    if "equals" in when:
        matched = condition_value == when["equals"]

    elif "not_equals" in when:
        matched = condition_value != when["not_equals"]

    elif "in" in when:
        allowed = when["in"]

        if not isinstance(allowed, (list, tuple, set)):
            return False, f"'in' for '{condition_path}' must be a collection."

        matched = condition_value in allowed

    elif "not_in" in when:
        disallowed = when["not_in"]

        if not isinstance(disallowed, (list, tuple, set)):
            return False, f"'not_in' for '{condition_path}' must be a collection."

        matched = condition_value not in disallowed

    elif "truthy" in when:
        if not isinstance(when["truthy"], bool):
            return False, "'truthy' must be boolean."

        matched = bool(condition_value) == when["truthy"]

    else:
        return (
            False,
            f"Dependency for '{condition_path}' has no valid condition."
        )

    # Dependency is inactive when its condition does not match.
    if not matched:
        return True, ""

    missing = []

    for required_path in requires:
        if not isinstance(required_path, str) or not required_path.strip():
            return False, "Dependency paths must be non-empty strings."

        _, exists = get_nested_value(config, required_path)

        if not exists:
            missing.append(required_path)

    if missing:
        return (
            False,
            f"Dependency failed: when '{condition_path}' is active, "
            f"missing required field(s): {', '.join(missing)}."
        )

    return True, ""


def validate_config(
    config: Dict[str, Any],
    rules: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate configuration rules and cross-field dependencies."""
    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    if not isinstance(rules, list):
        return {
            "valid": False,
            "errors": ["Rules must be a list."]
        }

    if dependencies is None:
        dependencies = []

    if not isinstance(dependencies, list):
        return {
            "valid": False,
            "errors": ["Dependencies must be a list."]
        }

    errors = []

    # Validate individual fields.
    for index, rule in enumerate(rules):
        valid, error = validate_rule(config, rule)

        if not valid:
            errors.append(error or f"Rule {index} failed.")

    # Validate cross-field dependencies.
    for index, dependency in enumerate(dependencies):
        valid, error = validate_dependency(config, dependency)

        if not valid:
            errors.append(error or f"Dependency {index} failed.")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    config = {
        "server": {
            "enabled": True,
            "port": 65535,
            "limits": {
                "connections": 1
            }
        },
        "database": {
            "type": "postgres",
            "host": "localhost"
        }
    }

    rules = [
        # Exact boundary values are valid.
        {
            "path": "server.port",
            "type": "int",
            "min": 1,
            "max": 65535,
            "required": True
        },
        {
            "path": "server.limits.connections",
            "type": "int",
            "min": 1,
            "max": 1000,
            "required": True
        },

        # Optional missing field is valid.
        {
            "path": "server.timeout",
            "type": "int",
            "min": 0,
            "max": 60,
            "required": False
        },

        # Required missing field is invalid.
        {
            "path": "database.port",
            "type": "int",
            "min": 1,
            "max": 65535,
            "required": True
        }
    ]

    dependencies = [
        {
            "when": {
                "path": "server.enabled",
                "equals": True
            },
            "requires": [
                "server.port"
            ]
        },
        {
            "when": {
                "path": "database.type",
                "in": ["mysql", "postgres"]
            },
            "requires": [
                "database.host",
                "database.port"
            ]
        }
    ]

    print(validate_config(config, rules, dependencies))