from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Project, ProjectMember
from .serializers import (
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectMemberReadSerializer,
    AddMemberSerializer,
    UpdateMemberRoleSerializer,
)
from .permissions import CanCreateProject, CanListAllProject, CanAccessProject
from accounts.enums import UserRole


class ProjectViewSet(ModelViewSet):

    def get_queryset(self):
        user = self.request.user
        qs = Project.objects.select_related("form_schema__form_type", "created_by")
        if user.role in [UserRole.LEAD, UserRole.EMPLOYEE]:
            return qs.filter(projectmember__user=user)
        return qs.all()

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanCreateProject()]
        if self.action in ("members", "remove_member", "update_member_role"):
            return [IsAuthenticated(), CanCreateProject()]
        return [IsAuthenticated(), CanAccessProject()]

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in ("update", "partial_update"):
            return ProjectUpdateSerializer
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectListSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        output = ProjectListSerializer(instance, context={"request": request})
        return Response(output.data, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=["delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def remove_member(self, request, pk=None, member_id=None):
        project = self.get_object()

        try:
            member = ProjectMember.objects.get(project=project, id=member_id)
        except ProjectMember.DoesNotExist:
            return Response(
                {"detail": "Member not found in this project."},
                status=status.HTTP_404_NOT_FOUND,
            )

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path=r"members/(?P<member_id>[^/.]+)/role")
    def update_member_role(self, request, pk=None, member_id=None):
        project = self.get_object()

        try:
            member = ProjectMember.objects.select_related("user").get(project=project, id=member_id)
        except ProjectMember.DoesNotExist:
            return Response(
                {"detail": "Member not found in this project."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UpdateMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member.role = serializer.validated_data["role"]
        member.save(update_fields=["role"])

        return Response(ProjectMemberReadSerializer(member).data, status=status.HTTP_200_OK)
