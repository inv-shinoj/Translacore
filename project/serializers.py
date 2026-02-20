from rest_framework import serializers
from forms.models import FormSchema
from forms.enums import SchemaStatus
from .models import Project
from .enums import ProjectStatus
from .validators import validate_project_data


class ProjectListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    form_type_name = serializers.CharField(
        source="form_schema.form_type.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "status",
            "status_display",
            "form_type_name",
            "created_by_name",
            "created_at",
            "updated_at",
        )


class ProjectCreateSerializer(serializers.ModelSerializer):
    form_type = serializers.IntegerField(write_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "form_type", "project_data")

    def validate(self, attrs):
        form_type_key = attrs.pop("form_type")
        project_data = attrs["project_data"]

        # Get ACTIVE schema for that type
        schema = (
            FormSchema.objects
            .filter(
                form_type__key=form_type_key,
                status=SchemaStatus.ACTIVE
            )
            .first()
        )

        if not schema:
            raise serializers.ValidationError(
                "No active schema for selected form type"
            )

        validate_project_data(schema.schema_json, project_data)
        attrs["form_schema"] = schema
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user

        project = Project.objects.create(
            **validated_data,
            created_by=user,
            status=ProjectStatus.ACTIVE
        )

        return project
