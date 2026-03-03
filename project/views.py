from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Project, ProjectMember
from .serializers import (
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectMemberReadSerializer,
    AddMemberSerializer,
)
from .permissions import CanCreateProject, CanListAllProject, CanAccessProject


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.select_related(
        "form_schema__form_type", "created_by"
    ).all()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanCreateProject()]
        if self.action == "members":
            return [IsAuthenticated(), CanCreateProject()]
        return [IsAuthenticated(), CanAccessProject()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProjectCreateSerializer
        return ProjectListSerializer

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        project = self.get_object()

        if request.method == "GET":
            members = ProjectMember.objects.select_related("user").filter(project=project)
            return Response(ProjectMemberReadSerializer(members, many=True).data)

        # POST — add a member
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user_id"]   # validate_user_id returns User obj
        role = serializer.validated_data["role"]

        member, created = ProjectMember.objects.get_or_create(
            project=project,
            user=user,
            defaults={"role": role},
        )
        if not created:
            return Response(
                {"detail": "User is already a member of this project."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ProjectMemberReadSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )
