from rest_framework.permissions import BasePermission
from accounts.enums import UserRole
from project.models import ProjectMember


class CanAccessProjectDocuments(BasePermission):
    """
    Admin / Manager → access all project documents.
    Lead / Employee → only if they are a member of the project.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Admins and Managers can access any project's documents
        if user.role in (UserRole.ADMIN, UserRole.MANAGER):
            return True

        # Lead / Employee must be a member of the project
        project_id = view.kwargs.get("project_id")
        if not project_id:
            return False

        return ProjectMember.objects.filter(
            project_id=project_id,
            user=user,
        ).exists()


class CanDeleteDocument(BasePermission):
    """Only Admin or Manager can delete documents."""

    def has_permission(self, request, view):
        return request.user.role in (UserRole.ADMIN, UserRole.MANAGER)
