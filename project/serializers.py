from rest_framework import serializers
from forms.models import FormSchema
from forms.enums import SchemaStatus
from .models import Project, ProjectMember
from .enums import ProjectStatus
from .validators import validate_project_data
from accounts.models import User
from documents.enums import DocumentStatus


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


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "project_data", "status")
        extra_kwargs = {
            "name": {"required": False},
            "project_data": {"required": False},
            "status": {"required": False},
        }

    def validate_name(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("Project name cannot be empty.")
        return value.strip()

    def _validate_status_transition(self, current_status, next_status, project):
        if current_status == next_status:
            return

        allowed_transitions = {
            ProjectStatus.DRAFT: {ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED},
            ProjectStatus.ACTIVE: {ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED},
            ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED},
            ProjectStatus.ARCHIVED: set(),
        }

        if next_status not in allowed_transitions.get(current_status, set()):
            raise serializers.ValidationError(
                {
                    "status": (
                        f"Invalid status transition from '{ProjectStatus(current_status).label}' "
                        f"to '{ProjectStatus(next_status).label}'."
                    )
                }
            )

        if next_status == ProjectStatus.COMPLETED:
            docs = project.documents.all()
            if not docs.exists():
                raise serializers.ValidationError(
                    {"status": "Project must have at least one document before marking as Completed."}
                )

            has_non_completed = docs.exclude(status=DocumentStatus.COMPLETED).exists()
            if has_non_completed:
                raise serializers.ValidationError(
                    {"status": "All project documents must be Completed before completing the project."}
                )

        if next_status == ProjectStatus.ARCHIVED:
            has_translating = project.documents.filter(status=DocumentStatus.TRANSLATING).exists()
            if has_translating:
                raise serializers.ValidationError(
                    {"status": "Cannot archive while documents are still Translating."}
                )

    def validate(self, attrs):
        project = self.instance

        if not project:
            return attrs

        if project.status in (ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED):
            has_content_edits = "name" in attrs or "project_data" in attrs
            if has_content_edits:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "Completed or Archived projects are read-only. "
                            "Only allowed status transitions can be applied."
                        )
                    }
                )

        merged_project_data = attrs.get("project_data", project.project_data)
        validate_project_data(project.form_schema.schema_json, merged_project_data)

        if "status" in attrs:
            self._validate_status_transition(project.status, attrs["status"], project)

        return attrs


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


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[(2, "Lead"), (3, "Employee")])
