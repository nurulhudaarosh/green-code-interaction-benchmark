from typing import Any, Dict, List


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Safely retrieve a value using a dotted nested path."""
    if not isinstance(data, dict) or not isinstance(path, str) or not path.strip():
        return None

    current = data
    for key in path.split("."):
        key = key.strip()
        if not key or not isinstance(current, dict) or key not in current:
            return None
        current = current[key]

    return current


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate supported types, treating bool separately from int."""
    expected_type = expected_type.lower().strip()

    if expected_type == "string":
        return isinstance(value, str)

    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)

    if expected_type == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    if expected_type == "boolean":
        return isinstance(value, bool)

    if expected_type == "object":
        return isinstance(value, dict)

    if expected_type == "array":
        return isinstance(value, list)

    if expected_type == "null":
        return value is None

    return False


def validate_config(
    config: Dict[str, Any],
    rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate configuration values against rules.

    Each rule can contain:
        path: nested path such as "database.host"
        required: True/False
        type: string, integer, number, boolean, object, array, null
        allowed: optional list of allowed values
    """
    errors = []

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    for rule in rules:
        if not isinstance(rule, dict):
            errors.append("Invalid validation rule.")
            continue

        path = rule.get("path")
        required = rule.get("required", False)
        expected_type = rule.get("type")
        allowed = rule.get("allowed")

        if not isinstance(path, str) or not path.strip():
            errors.append("Validation rule is missing a valid path.")
            continue

        value = get_nested_value(config, path)

        # Determine whether the path actually exists.
        current = config
        exists = True

        for key in path.split("."):
            key = key.strip()
            if not key or not isinstance(current, dict) or key not in current:
                exists = False
                break
            current = current[key]

        if not exists:
            if required:
                errors.append(f"Missing required field: {path}")
            continue

        if expected_type is not None:
            if not validate_type(value, expected_type):
                errors.append(
                    f"Invalid type for {path}: "
                    f"expected {expected_type}, got {type(value).__name__}"
                )
                continue

        if allowed is not None and value not in allowed:
            errors.append(
                f"Invalid value for {path}: {value!r}. "
                f"Expected one of {allowed!r}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# Example usage
if __name__ == "__main__":
    config = {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "features": {
            "enabled": True
        },
        "debug": False
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
            "path": "features.enabled",
            "required": True,
            "type": "boolean"
        },
        {
            "path": "debug",
            "required": True,
            "type": "boolean"
        }
    ]

    result = validate_config(config, rules)
    print(result)