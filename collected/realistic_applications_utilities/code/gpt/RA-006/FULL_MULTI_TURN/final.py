from typing import Any, Dict, List, Tuple


def _get_nested(config: Dict[str, Any], path: str) -> Tuple[bool, Any]:
    current = config

    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    return True, current


def _is_exact_type(value: Any, expected_type: type) -> bool:
    # Prevent bool from being accepted as int.
    return type(value) is expected_type


def validate_configuration(config: Any) -> Dict[str, Any]:
    errors: List[str] = []

    if not isinstance(config, dict):
        return {
            "valid": False,
            "errors": ["Configuration must be a dictionary."]
        }

    # Required top-level fields.
    required = {
        "name": str,
        "enabled": bool,
        "settings": dict,
    }

    for field, expected_type in required.items():
        if field not in config:
            errors.append(f"Missing required field: {field}.")
        elif not _is_exact_type(config[field], expected_type):
            errors.append(
                f"Field '{field}' must be of type {expected_type.__name__}."
            )

    # Name validation.
    if "name" in config and _is_exact_type(config["name"], str):
        if not config["name"].strip():
            errors.append("Field 'name' cannot be empty.")

    settings_exists, settings = _get_nested(config, "settings")

    if settings_exists and isinstance(settings, dict):
        # Required nested fields.
        nested_required = {
            "settings.timeout": int,
            "settings.retries": int,
            "settings.logging": dict,
        }

        for path, expected_type in nested_required.items():
            exists, value = _get_nested(config, path)

            if not exists:
                errors.append(f"Missing required field: {path}.")
            elif not _is_exact_type(value, expected_type):
                errors.append(
                    f"Field '{path}' must be of type "
                    f"{expected_type.__name__}."
                )

        # Boundary validation.
        exists, timeout = _get_nested(config, "settings.timeout")
        if exists and _is_exact_type(timeout, int):
            if timeout < 0:
                errors.append(
                    "Field 'settings.timeout' must be greater than or equal to 0."
                )

        exists, retries = _get_nested(config, "settings.retries")
        if exists and _is_exact_type(retries, int):
            if retries < 0:
                errors.append(
                    "Field 'settings.retries' must be greater than or equal to 0."
                )

        # Deeper logging validation.
        logging_exists, logging = _get_nested(
            config, "settings.logging"
        )

        if logging_exists and isinstance(logging, dict):
            logging_required = {
                "settings.logging.enabled": bool,
                "settings.logging.level": str,
            }

            for path, expected_type in logging_required.items():
                exists, value = _get_nested(config, path)

                if not exists:
                    errors.append(f"Missing required field: {path}.")
                elif not _is_exact_type(value, expected_type):
                    errors.append(
                        f"Field '{path}' must be of type "
                        f"{expected_type.__name__}."
                    )

            exists, level = _get_nested(
                config, "settings.logging.level"
            )
            if exists and _is_exact_type(level, str):
                if not level.strip():
                    errors.append(
                        "Field 'settings.logging.level' cannot be empty."
                    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


if __name__ == "__main__":
    # Valid boundary values: 0 is allowed.
    valid_config = {
        "name": "my_app",
        "enabled": True,
        "settings": {
            "timeout": 0,
            "retries": 0,
            "logging": {
                "enabled": False,
                "level": "INFO",
            },
        },
    }

    # Missing fields and invalid boundaries.
    invalid_config = {
        "name": "my_app",
        "enabled": True,
        "settings": {
            "timeout": -1,
            "logging": {
                "enabled": True,
            },
        },
    }

    print(validate_configuration(valid_config))
    print(validate_configuration(invalid_config))