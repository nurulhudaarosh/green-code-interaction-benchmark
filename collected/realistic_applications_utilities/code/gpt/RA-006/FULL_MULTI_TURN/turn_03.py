from typing import Any, Dict, List


def _validate_type(value: Any, expected_type: type) -> bool:
    """Strictly validate types, especially bool vs int."""
    return type(value) is expected_type


def _get_nested(config: Dict[str, Any], path: str):
    """Safely retrieve a nested configuration value."""
    current = config

    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    return True, current


def validate_configuration(config: Any) -> Dict[str, Any]:
    """
    Validate configuration with nested-path and strict type handling.

    Expected structure:
    {
        "name": str,
        "enabled": bool,
        "settings": {
            "timeout": int,
            "retries": int,
            "logging": {
                "enabled": bool,
                "level": str
            }
        }
    }
    """
    errors: List[str] = []

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    # Required top-level fields and strict types.
    required_fields = {
        "name": str,
        "enabled": bool,
        "settings": dict,
    }

    for field, expected_type in required_fields.items():
        if field not in config:
            errors.append(f"Missing required field: {field}.")
        elif not _validate_type(config[field], expected_type):
            errors.append(
                f"Field '{field}' must be of type "
                f"{expected_type.__name__}."
            )

    # Validate name.
    if "name" in config and _validate_type(config["name"], str):
        if not config["name"].strip():
            errors.append("Field 'name' cannot be empty.")

    # Nested settings validation.
    settings_exists, settings = _get_nested(config, "settings")

    if settings_exists and isinstance(settings, dict):
        nested_rules = {
            "settings.timeout": int,
            "settings.retries": int,
            "settings.logging": dict,
        }

        for path, expected_type in nested_rules.items():
            exists, value = _get_nested(config, path)

            if not exists:
                errors.append(f"Missing required field: {path}.")
            elif not _validate_type(value, expected_type):
                errors.append(
                    f"Field '{path}' must be of type "
                    f"{expected_type.__name__}."
                )

        # Validate numeric boundaries only after type validation.
        exists, timeout = _get_nested(config, "settings.timeout")
        if exists and _validate_type(timeout, int) and timeout < 0:
            errors.append("Field 'settings.timeout' cannot be negative.")

        exists, retries = _get_nested(config, "settings.retries")
        if exists and _validate_type(retries, int) and retries < 0:
            errors.append("Field 'settings.retries' cannot be negative.")

        # Validate deeper nested fields.
        logging_exists, logging = _get_nested(
            config, "settings.logging"
        )

        if logging_exists and isinstance(logging, dict):
            logging_rules = {
                "settings.logging.enabled": bool,
                "settings.logging.level": str,
            }

            for path, expected_type in logging_rules.items():
                exists, value = _get_nested(config, path)

                if not exists:
                    errors.append(f"Missing required field: {path}.")
                elif not _validate_type(value, expected_type):
                    errors.append(
                        f"Field '{path}' must be of type "
                        f"{expected_type.__name__}."
                    )

            exists, level = _get_nested(
                config, "settings.logging.level"
            )
            if exists and _validate_type(level, str):
                if not level.strip():
                    errors.append(
                        "Field 'settings.logging.level' cannot be empty."
                    )

    return {
        "valid": not errors,
        "errors": errors,
    }


if __name__ == "__main__":
    valid_config = {
        "name": "my_app",
        "enabled": True,
        "settings": {
            "timeout": 30,
            "retries": 3,
            "logging": {
                "enabled": True,
                "level": "INFO",
            },
        },
    }

    invalid_config = {
        "name": "my_app",
        "enabled": 1,  # Invalid: int is not accepted as bool.
        "settings": {
            "timeout": True,  # Invalid: bool is not accepted as int.
            "retries": -1,
            "logging": {
                "enabled": "true",
                "level": "",
            },
        },
    }

    print(validate_configuration(valid_config))
    print(validate_configuration(invalid_config))