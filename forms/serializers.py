from rest_framework import serializers
import json
from .models import FormType, FormSchema
from .validators import validate_form_schema, SchemaValidationError
from .enums import FormTypeKey

class FormTypeSerializer(serializers.ModelSerializer):
    key = serializers.ChoiceField(choices=FormTypeKey.choices)

    class Meta:
        model = FormType
        fields = ("id", "key", "name", "description", "is_active")


class FormSchemaCreateSerializer(serializers.ModelSerializer):
    schema_file = serializers.FileField(
        write_only=True,
        required=False
    )

    status = serializers.CharField(
        source="get_status_display",
        read_only=True
    )
    
    form_type = serializers.SlugRelatedField(
        slug_field="key",               
        queryset=FormType.objects.all()
    )

    class Meta:
        model = FormSchema
        fields = (
            "id",
            "form_type",
            "name",
            "schema_json",
            "schema_file",
            "version",
            "status",
        )
        extra_kwargs = {
            "schema_json": {"required": False}
        }

    def validate(self, attrs):
        schema_file = attrs.pop("schema_file", None)
        schema_json = attrs.get("schema_json")

        # Enforce one source
        if not schema_file and not schema_json:
            raise serializers.ValidationError(
                "Provide either schema_file or schema_json"
            )

        if schema_file:
            try:
                schema_json = json.load(schema_file)
            except Exception:
                raise serializers.ValidationError(
                    "Invalid JSON file"
                )

        try:
            validate_form_schema(schema_json)
        except SchemaValidationError as e:
            raise serializers.ValidationError(str(e))

        attrs["schema_json"] = schema_json
        return attrs

    def create(self, validated_data):
        form_type = validated_data["form_type"]

        latest = (
            FormSchema.objects
            .filter(form_type=form_type)
            .order_by("-version")
            .first()
        )
        # form_type = FormType.objects.filter(key=form_type).first()
        # validated_data['form_type'] = form_type
        # print("Form type:",form_type)
        validated_data["version"] = 1 if not latest else latest.version + 1
        validated_data["created_by"] = self.context["request"].user


        return super().create(validated_data)
    