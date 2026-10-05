from typing import Any, Dict, List, Tuple


class ValidationError:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"path": self.path, "message": self.message}


def get_nested_value(data: Dict[str, Any], path: str) -> Tuple[bool, Any]:
    if not isinstance(data, dict):
        return False, None

    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]

    return True, current


def is_empty(value: Any) -> bool:
    return (
        value is None
        or (isinstance(value, str) and not value.strip())
    )


def check_type(value: Any, expected_type: str) -> bool:
    # bool is deliberately excluded from integer/number validation.
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)

    return True


def validate_field(
    data: Dict[str, Any],
    path: str,
    rules: Dict[str, Any],
    errors: List[ValidationError],
) -> None:
    exists, value = get_nested_value(data, path)

    if rules.get("required") and not exists:
        errors.append(ValidationError(path, "Field is required."))
        return

    if not exists:
        return

    expected_type = rules.get("type")
    if expected_type and not check_type(value, expected_type):
        errors.append(
            ValidationError(
                path,
                f"Expected type '{expected_type}'.",
            )
        )
        return

    if "min" in rules and isinstance(value, (int, float)):
        if value < rules["min"]:
            errors.append(
                ValidationError(
                    path,
                    f"Value must be at least {rules['min']}.",
                )
            )

    if "max" in rules and isinstance(value, (int, float)):
        if value > rules["max"]:
            errors.append(
                ValidationError(
                    path,
                    f"Value must be at most {rules['max']}.",
                )
            )

    if "min_length" in rules and isinstance(value, (str, list)):
        if len(value) < rules["min_length"]:
            errors.append(
                ValidationError(
                    path,
                    f"Length must be at least {rules['min_length']}.",
                )
            )

    if "max_length" in rules and isinstance(value, (str, list)):
        if len(value) > rules["max_length"]:
            errors.append(
                ValidationError(
                    path,
                    f"Length must be at most {rules['max_length']}.",
                )
            )

    if "choices" in rules and value not in rules["choices"]:
        errors.append(
            ValidationError(
                path,
                f"Value must be one of {rules['choices']}.",
            )
        )


def validate_cross_field_dependencies(
    data: Dict[str, Any],
    dependencies: List[Dict[str, Any]],
    errors: List[ValidationError],
) -> None:
    """
    Supported dependency formats:

    1. Conditional required:
       {
           "when": "account.type",
           "equals": "business",
           "then_required": "account.company_name"
       }

    2. Required when any field has a value:
       {
           "when_any": ["email", "phone"],
           "then_required": "contact_name"
       }

    3. Required when all conditions are true:
       {
           "when_all": ["is_student", "has_id"],
           "equals": True,
           "then_required": "student_id"
       }

    4. Field comparison:
       {
           "fields": ["password", "confirm_password"],
           "rule": "equals"
       }

    5. Numeric/date-style comparisons:
       rule = greater_than
       rule = greater_than_or_equal
       rule = less_than
       rule = less_than_or_equal
    """

    for dependency in dependencies:
        # ---------------------------------------------------------
        # required_if
        # ---------------------------------------------------------
        if "when" in dependency and "then_required" in dependency:
            source_path = dependency["when"]
            target_path = dependency["then_required"]

            source_exists, source_value = get_nested_value(
                data, source_path
            )

            condition_met = source_exists

            if "equals" in dependency:
                condition_met = (
                    source_exists
                    and source_value == dependency["equals"]
                )

            if condition_met:
                target_exists, target_value = get_nested_value(
                    data, target_path
                )

                if not target_exists or is_empty(target_value):
                    errors.append(
                        ValidationError(
                            target_path,
                            f"Field is required when '{source_path}' "
                            f"meets the dependency condition.",
                        )
                    )

        # ---------------------------------------------------------
        # required_if_any
        # ---------------------------------------------------------
        if "when_any" in dependency and "then_required" in dependency:
            target_path = dependency["then_required"]
            condition_met = False

            for source_path in dependency["when_any"]:
                exists, value = get_nested_value(data, source_path)

                if exists and not is_empty(value):
                    condition_met = True
                    break

            if condition_met:
                target_exists, target_value = get_nested_value(
                    data, target_path
                )

                if not target_exists or is_empty(target_value):
                    errors.append(
                        ValidationError(
                            target_path,
                            "Field is required because at least one "
                            "dependency field has a value.",
                        )
                    )

        # ---------------------------------------------------------
        # required_if_all
        # ---------------------------------------------------------
        if "when_all" in dependency and "then_required" in dependency:
            target_path = dependency["then_required"]
            condition_met = True

            for source_path in dependency["when_all"]:
                exists, value = get_nested_value(data, source_path)

                if not exists or is_empty(value):
                    condition_met = False
                    break

                if "equals" in dependency:
                    if value != dependency["equals"]:
                        condition_met = False
                        break

            if condition_met:
                target_exists, target_value = get_nested_value(
                    data, target_path
                )

                if not target_exists or is_empty(target_value):
                    errors.append(
                        ValidationError(
                            target_path,
                            "Field is required because all dependency "
                            "conditions are satisfied.",
                        )
                    )

        # ---------------------------------------------------------
        # Cross-field comparisons
        # ---------------------------------------------------------
        if "fields" in dependency:
            fields = dependency["fields"]

            if not isinstance(fields, list) or len(fields) != 2:
                continue

            first_path, second_path = fields

            first_exists, first_value = get_nested_value(
                data, first_path
            )
            second_exists, second_value = get_nested_value(
                data, second_path
            )

            # Do not report comparison errors if one side is missing.
            # Required validation handles missing fields separately.
            if not first_exists or not second_exists:
                continue

            rule = dependency.get("rule")

            try:
                valid = True

                if rule == "equals":
                    valid = first_value == second_value

                elif rule == "not_equals":
                    valid = first_value != second_value

                elif rule == "greater_than":
                    valid = first_value > second_value

                elif rule == "greater_than_or_equal":
                    valid = first_value >= second_value

                elif rule == "less_than":
                    valid = first_value < second_value

                elif rule == "less_than_or_equal":
                    valid = first_value <= second_value

                else:
                    continue

            except TypeError:
                errors.append(
                    ValidationError(
                        first_path,
                        f"Fields '{first_path}' and '{second_path}' "
                        "must contain comparable values.",
                    )
                )
                continue

            if not valid:
                messages = {
                    "equals": f"'{first_path}' must equal '{second_path}'.",
                    "not_equals": (
                        f"'{first_path}' must not equal '{second_path}'."
                    ),
                    "greater_than": (
                        f"'{first_path}' must be greater than "
                        f"'{second_path}'."
                    ),
                    "greater_than_or_equal": (
                        f"'{first_path}' must be greater than or equal to "
                        f"'{second_path}'."
                    ),
                    "less_than": (
                        f"'{first_path}' must be less than "
                        f"'{second_path}'."
                    ),
                    "less_than_or_equal": (
                        f"'{first_path}' must be less than or equal to "
                        f"'{second_path}'."
                    ),
                }

                errors.append(
                    ValidationError(
                        first_path,
                        messages.get(
                            rule,
                            "Cross-field dependency failed.",
                        ),
                    )
                )


def validate_configuration(
    data: Dict[str, Any],
    configuration: Dict[str, Any],
) -> Dict[str, Any]:
    errors: List[ValidationError] = []

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": [
                {
                    "path": "",
                    "message": "Input data must be an object.",
                }
            ],
        }

    if not isinstance(configuration, dict):
        return {
            "valid": False,
            "errors": [
                {
                    "path": "",
                    "message": "Configuration must be an object.",
                }
            ],
        }

    # Field-level validation
    fields = configuration.get("fields", {})

    if isinstance(fields, dict):
        for path, rules in fields.items():
            if isinstance(path, str) and isinstance(rules, dict):
                validate_field(data, path, rules, errors)

    # Cross-field dependency validation
    dependencies = configuration.get("dependencies", [])

    if isinstance(dependencies, list):
        validate_cross_field_dependencies(
            data,
            dependencies,
            errors,
        )

    return {
        "valid": len(errors) == 0,
        "errors": [error.to_dict() for error in errors],
    }


if __name__ == "__main__":
    configuration = {
        "fields": {
            "user.name": {
                "required": True,
                "type": "string",
                "min_length": 2,
            },
            "user.age": {
                "required": True,
                "type": "integer",
                "min": 18,
            },
            "account.is_business": {
                "required": True,
                "type": "boolean",
            },
        },
        "dependencies": [
            {
                "when": "account.is_business",
                "equals": True,
                "then_required": "account.company_name",
            },
            {
                "fields": ["password", "confirm_password"],
                "rule": "equals",
            },
            {
                "fields": ["end_value", "start_value"],
                "rule": "greater_than_or_equal",
            },
        ],
    }

    data = {
        "user": {
            "name": "Sam",
            "age": 22,
        },
        "account": {
            "is_business": True,
        },
        "password": "secret123",
        "confirm_password": "secret456",
        "start_value": 10,
        "end_value": 5,
    }

    result = validate_configuration(data, configuration)
    print(result)