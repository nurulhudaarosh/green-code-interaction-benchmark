from typing import Any, Dict, List, Tuple


def get_nested_value(config: Any, path: str) -> Tuple[bool, Any]:
    current = config

    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    return True, current


def is_exact_type(value: Any, expected_type: type) -> bool:
    # Prevent bool from being treated as int.
    return type(value) is expected_type


def validate_configuration(config: Any) -> Dict[str, Any]:
    errors: List[str] = []

    # Empty / invalid configuration handling.
    if config is None:
        return {
            "valid": False,
            "errors": ["Configuration cannot be None."]
        }

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    if not config:
        return {
            "valid": False,
            "errors": ["Configuration cannot be empty."]
        }

    # Required top-level fields.
    top_level_rules = {
        "name": str,
        "enabled": bool,
        "settings": dict,
    }

    for path, expected_type in top_level_rules.items():
        exists, value = get_nested_value(config, path)

        if not exists:
            errors.append(f"Missing required field: {path}.")
        elif not is_exact_type(value, expected_type):
            errors.append(
                f"Field '{path}' must be of type "
                f"{expected_type.__name__}."
            )

    # Validate name.
    exists, name = get_nested_value(config, "name")

    if exists and is_exact_type(name, str) and not name.strip():
        errors.append("Field 'name' cannot be empty.")

    settings_exists, settings = get_nested_value(config, "settings")

    # Do not traverse invalid/missing settings.
    if not settings_exists or not is_exact_type(settings, dict):
        return {
            "valid": not errors,
            "errors": errors,
        }

    # Required nested fields.
    nested_rules = {
        "settings.timeout": int,
        "settings.retries": int,
        "settings.logging": dict,
    }

    for path, expected_type in nested_rules.items():
        exists, value = get_nested_value(config, path)

        if not exists:
            errors.append(f"Missing required field: {path}.")
        elif not is_exact_type(value, expected_type):
            errors.append(
                f"Field '{path}' must be of type "
                f"{expected_type.__name__}."
            )

    # Boundary values: 0 is valid, negative values are invalid.
    exists, timeout = get_nested_value(config, "settings.timeout")

    if exists and is_exact_type(timeout, int) and timeout < 0:
        errors.append(
            "Field 'settings.timeout' must be greater than or equal to 0."
        )

    exists, retries = get_nested_value(config, "settings.retries")

    if exists and is_exact_type(retries, int) and retries < 0:
        errors.append(
            "Field 'settings.retries' must be greater than or equal to 0."
        )

    # Logging fields.
    logging_exists, logging = get_nested_value(
        config, "settings.logging"
    )

    if logging_exists and is_exact_type(logging, dict):
        logging_rules = {
            "settings.logging.enabled": bool,
            "settings.logging.level": str,
        }

        for path, expected_type in logging_rules.items():
            exists, value = get_nested_value(config, path)

            if not exists:
                errors.append(f"Missing required field: {path}.")
            elif not is_exact_type(value, expected_type):
                errors.append(
                    f"Field '{path}' must be of type "
                    f"{expected_type.__name__}."
                )

        exists, level = get_nested_value(
            config, "settings.logging.level"
        )

        if exists and is_exact_type(level, str) and not level.strip():
            errors.append(
                "Field 'settings.logging.level' cannot be empty."
            )

    # Cross-field dependency: disabled application cannot have
    # logging enabled or non-zero retries.
    app_exists, app_enabled = get_nested_value(config, "enabled")
    logging_enabled_exists, logging_enabled = get_nested_value(
        config, "settings.logging.enabled"
    )

    if (
        app_exists
        and logging_enabled_exists
        and is_exact_type(app_enabled, bool)
        and is_exact_type(logging_enabled, bool)
        and app_enabled is False
        and logging_enabled is True
    ):
        errors.append(
            "Logging cannot be enabled when the application is disabled."
        )

    if (
        app_exists
        and is_exact_type(app_enabled, bool)
        and app_enabled is False
    ):
        retries_exists, retries = get_nested_value(
            config, "settings.retries"
        )

        if (
            retries_exists
            and is_exact_type(retries, int)
            and retries != 0
        ):
            errors.append(
                "Retries must be 0 when the application is disabled."
            )

    return {
        "valid": not errors,
        "errors": errors,
    }


if __name__ == "__main__":
    test_cases = [
        # Empty configuration.
        {},

        # Valid boundary values.
        {
            "name": "app",
            "enabled": True,
            "settings": {
                "timeout": 0,
                "retries": 0,
                "logging": {
                    "enabled": False,
                    "level": "INFO",
                },
            },
        },

        # Missing nested paths.
        {
            "name": "app",
            "enabled": True,
            "settings": {
                "timeout": 10,
            },
        },

        # Mixed types.
        {
            "name": 123,
            "enabled": 1,
            "settings": {
                "timeout": True,
                "retries": "3",
                "logging": {
                    "enabled": "true",
                    "level": 10,
                },
            },
        },

        # Negative boundary values.
        {
            "name": "app",
            "enabled": True,
            "settings": {
                "timeout": -1,
                "retries": -1,
                "logging": {
                    "enabled": False,
                    "level": "INFO",
                },
            },
        },
    ]

    for index, config in enumerate(test_cases, 1):
        print(f"Test {index}:")
        print(validate_configuration(config))
        print()