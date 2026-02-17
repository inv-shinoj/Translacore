from rest_framework.permissions import BasePermission
from accounts.enums import UserRole


class CanCreateProject(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.MANAGER,
            UserRole.LEAD
        ]
