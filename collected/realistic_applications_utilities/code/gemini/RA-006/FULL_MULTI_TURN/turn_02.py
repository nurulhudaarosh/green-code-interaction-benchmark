from typing import Any, Dict, List, Tuple


def get_nested_value(config: Dict[str, Any], path: str) -> Tuple[Any, bool]:
    """Safely retrieve a nested value using dot notation."""
    if not isinstance(config, dict) or not isinstance(path, str) or not path.strip():
        return None, False

    current = config

    for part in path.split("."):
        part = part.strip()

        if not part or not isinstance(current, dict) or part not in current:
            return None, False

        current = current[part]

    return current, True


def matches_type(value: Any, expected_type: str) -> bool:
    """Check types strictly, including correct boolean handling."""
    if not isinstance(expected_type, str):
        return False

    expected_type = expected_type.lower().strip()

    type_map = {
        "string": str,
        "str": str,
        "integer": int,
        "int": int,
        "float": float,
        "number": (int, float),
        "boolean": bool,
        "bool": bool,
        "list": list,
        "dict": dict,
        "object": dict,
    }

    expected = type_map.get(expected_type)

    if expected is None:
        return False

    # bool is a subclass of int in Python, so explicitly prevent
    # booleans from being accepted as integers/numbers.
    if expected_type in {"int", "integer", "number"} and isinstance(value, bool):
        return False

    # float means an actual float, not an integer.
    if expected_type == "float":
        return isinstance(value, float) and not isinstance(value, bool)

    return isinstance(value, expected)


def validate_rule(config: Dict[str, Any], rule: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single configuration rule."""
    if not isinstance(rule, dict):
        return False, "Rule must be a dictionary."

    path = rule.get("path")

    if not isinstance(path, str) or not path.strip():
        return False, "Rule path must be a non-empty string."

    value, exists = get_nested_value(config, path)

    required = rule.get("required", False)

    if not isinstance(required, bool):
        return False, f"Invalid required setting for '{path}'."

    if not exists:
        if required:
            return False, f"Required field '{path}' is missing."
        return True, ""

    expected_type = rule.get("type")

    if expected_type is not None:
        if not matches_type(value, expected_type):
            return (
                False,
                f"Field '{path}' has an invalid type. "
                f"Expected {expected_type}."
            )

    if "min" in rule:
        minimum = rule["min"]

        try:
            if value < minimum:
                return False, f"Field '{path}' is below the minimum value."
        except TypeError:
            return False, f"Minimum constraint is invalid for '{path}'."

    if "max" in rule:
        maximum = rule["max"]

        try:
            if value > maximum:
                return False, f"Field '{path}' exceeds the maximum value."
        except TypeError:
            return False, f"Maximum constraint is invalid for '{path}'."

    if "allowed" in rule:
        allowed = rule["allowed"]

        if not isinstance(allowed, (list, tuple, set)):
            return False, f"Allowed values for '{path}' must be a collection."

        if value not in allowed:
            return False, f"Field '{path}' contains a value that is not allowed."

    return True, ""


def validate_config(
    config: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Validate a complete configuration."""
    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    if not isinstance(rules, list):
        return {
            "valid": False,
            "errors": ["Validation rules must be a list."]
        }

    errors = []

    for index, rule in enumerate(rules):
        valid, error = validate_rule(config, rule)

        if not valid:
            errors.append(error or f"Validation failed for rule {index}.")

    return {
        "valid": not errors,
        "errors": errors
    }


if __name__ == "__main__":
    config = {
        "server": {
            "host": "localhost",
            "port": 8080,
            "debug": True,
            "limits": {
                "connections": 100
            }
        },
        "database": {
            "name": "app_db",
            "enabled": False
        }
    }

    rules = [
        {"path": "server.host", "type": "string", "required": True},
        {"path": "server.port", "type": "int", "min": 1, "max": 65535},
        {"path": "server.debug", "type": "bool"},
        {"path": "server.limits.connections", "type": "int", "min": 1},
        {"path": "database.name", "type": "string", "required": True},
        {"path": "database.enabled", "type": "bool"}
    ]

    result = validate_config(config, rules)
    print(result)