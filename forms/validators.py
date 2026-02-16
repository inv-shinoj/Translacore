class SchemaValidationError(Exception):
    pass


def validate_form_schema(schema: dict):
    if "fields" not in schema or not isinstance(schema["fields"], list):
        raise SchemaValidationError("Schema must contain a fields list")

    keys = set()

    for field in schema["fields"]:
        if "key" not in field or "type" not in field or "label" not in field:
            raise SchemaValidationError("Each field must have key, type, label")

        if field["key"] in keys:
            raise SchemaValidationError(f"Duplicate field key: {field['key']}")

        keys.add(field["key"])
