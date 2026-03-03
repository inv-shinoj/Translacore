from rest_framework.permissions import BasePermission
from accounts.enums import UserRole


class CanCreateProject(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.ADMIN,
            UserRole.MANAGER,
        ]


class CanListAllProject(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.ADMIN,
        ]


class CanAccessProject(BasePermission):
    """Read-only access for Admin and Manager; full access for Admin only."""
    def has_permission(self, request, view):
        if request.user.role == UserRole.ADMIN:
            return True
        if request.user.role == UserRole.MANAGER:
            return view.action in ("list", "retrieve", "members")
        return False
