from rest_framework.exceptions import ValidationError


def validate_project_data(schema_json: dict, project_data: dict):
    errors = {}

    schema_fields = schema_json.get("fields", [])
    schema_map = {field["key"]: field for field in schema_fields}

    # Required field validation
    for key, field in schema_map.items():
        if field.get("required") and key not in project_data:
            errors[key] = "This field is required."

    # Unknown field detection
    for key in project_data.keys():
        if key not in schema_map:
            errors[key] = "Unknown field."

    # Type & option validation
    for key, value in project_data.items():
        if key not in schema_map:
            continue

        field = schema_map[key]
        field_type = field["type"]

        if field_type in ("text", "textarea"):
            if not isinstance(value, str):
                errors[key] = "Must be a string."

        elif field_type == "select":
            options = field.get("options", [])
            if value not in options:
                errors[key] = f"Invalid option. Allowed: {options}"

        elif field_type == "date":
            if not isinstance(value, str):
                errors[key] = "Date must be in YYYY-MM-DD format."

        else:
            errors[key] = f"Unsupported field type: {field_type}"

    if errors:
        raise ValidationError(errors)
