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
    """Admin/Manager see all projects. Lead/Employee see only their assigned projects."""
    def has_permission(self, request, view):
        if request.user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True
        if request.user.role in [UserRole.LEAD, UserRole.EMPLOYEE]:
            return view.action in ("list", "retrieve")
        return False
