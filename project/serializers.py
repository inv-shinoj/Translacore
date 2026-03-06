from rest_framework import serializers
from forms.models import FormSchema
from forms.enums import SchemaStatus
from .models import Project, ProjectMember
from .enums import ProjectStatus
from .validators import validate_project_data
from accounts.models import User


class ProjectListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    form_type_name = serializers.CharField(
        source="form_schema.form_type.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "status",
            "status_display",
            "form_type_name",
            "created_by_name",
            "my_role",
            "created_at",
            "updated_at",
        )

    def get_my_role(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        member = obj.projectmember_set.filter(user=request.user).first()
        return member.get_role_display() if member else None


class ProjectDetailSerializer(ProjectListSerializer):
    """Extends list serializer with project_data and schema field definitions."""
    schema_fields = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + (
            "project_data",
            "schema_fields",
        )

    def get_schema_fields(self, obj):
        try:
            return obj.form_schema.schema_json.get("fields", [])
        except Exception:
            return []


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


class ProjectMemberReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ProjectMember
        fields = ("id", "full_name", "email", "role", "role_display", "assigned_at")


class AddMemberSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=[(2, "Lead"), (3, "Employee")])

    def validate_user_id(self, value):
        try:
            return User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
