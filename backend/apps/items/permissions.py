from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsReporterOrStaffOrReadOnly(BasePermission):
    """Public read, authenticated create, owner/staff update and delete."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return (
            request.user.is_staff
            or getattr(request.user, "role", "") == "ADMIN"
            or obj.reporter_id == request.user.id
        )
