from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.enums import UserRole


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )


class IsAdminOrReadOnlyForStaff(BasePermission):
    """Admin has full access. Manager and Lead have read-only access."""
    ALLOWED_READ_ROLES = {UserRole.ADMIN, UserRole.MANAGER, UserRole.LEAD}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return request.user.role in self.ALLOWED_READ_ROLES
        return request.user.role == UserRole.ADMIN
