from typing import Any, Dict, List


def get_nested_value(data: Dict[str, Any], path: str):
    """Return the value at a dotted path, or None if the path is missing."""
    if not isinstance(data, dict) or not isinstance(path, str):
        return None

    current = data
    for key in path.split("."):
        key = key.strip()
        if not key or not isinstance(current, dict) or key not in current:
            return None
        current = current[key]

    return current


def path_exists(data: Dict[str, Any], path: str) -> bool:
    """Check whether a nested dotted path exists."""
    if not isinstance(data, dict) or not isinstance(path, str):
        return False

    current = data
    for key in path.split("."):
        key = key.strip()
        if not key or not isinstance(current, dict) or key not in current:
            return False
        current = current[key]

    return True


def matches_type(value: Any, expected_type: str) -> bool:
    """Validate types while correctly separating bool from int."""
    if not isinstance(expected_type, str):
        return True

    expected_type = expected_type.strip().lower()

    if expected_type == "string":
        return isinstance(value, str)

    if expected_type == "boolean":
        return isinstance(value, bool)

    if expected_type == "integer":
        # bool is a subclass of int in Python, so exclude it explicitly.
        return isinstance(value, int) and not isinstance(value, bool)

    if expected_type in ("number", "float"):
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    if expected_type == "object":
        return isinstance(value, dict)

    if expected_type == "array":
        return isinstance(value, list)

    if expected_type == "null":
        return value is None

    return False


def validate_rule(config: Dict[str, Any], rule: Dict[str, Any]) -> List[str]:
    """Validate one configuration rule."""
    errors = []

    if not isinstance(rule, dict):
        return ["Invalid validation rule."]

    path = rule.get("path")
    required = rule.get("required", False)
    expected_type = rule.get("type")
    allowed = rule.get("allowed")

    if not isinstance(path, str) or not path.strip():
        return ["Validation rule must contain a valid path."]

    if not path_exists(config, path):
        if required:
            errors.append(f"Missing required field: {path}")
        return errors

    value = get_nested_value(config, path)

    if expected_type is not None:
        if not matches_type(value, expected_type):
            errors.append(
                f"Invalid type for '{path}': "
                f"expected {expected_type}, got {type(value).__name__}"
            )
            return errors

    if allowed is not None:
        if not isinstance(allowed, list):
            errors.append(f"'allowed' must be a list for '{path}'")
        elif value not in allowed:
            errors.append(
                f"Invalid value for '{path}': {value!r}; "
                f"expected one of {allowed!r}"
            )

    return errors


def validate_config(
    config: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Validate a configuration against all supplied rules."""
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

    errors = []

    for rule in rules:
        errors.extend(validate_rule(config, rule))

    return {
        "valid": not errors,
        "errors": errors
    }


if __name__ == "__main__":
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "options": {
                "ssl": True
            }
        },
        "features": {
            "enabled": False
        }
    }

    rules = [
        {
            "path": "database.host",
            "required": True,
            "type": "string"
        },
        {
            "path": "database.port",
            "required": True,
            "type": "integer"
        },
        {
            "path": "database.options.ssl",
            "required": True,
            "type": "boolean"
        },
        {
            "path": "features.enabled",
            "required": True,
            "type": "boolean"
        }
    ]

    print(validate_config(config, rules))