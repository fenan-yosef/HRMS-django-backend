from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_role(user, role: str) -> bool:
    return bool(getattr(user, "role", "").lower() == role)


def is_manager(user) -> bool:
    return is_role(user, "manager")


def is_hr_or_ceo(user) -> bool:
    return is_role(user, "hr") or is_role(user, "ceo") or user.is_superuser


class CanManageTasks(BasePermission):
    """Allow create/update/delete for HR, CEO, and Managers within scope. Read for authenticated users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        # create/update/delete guarded
        return is_hr_or_ceo(request.user) or is_manager(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if is_hr_or_ceo(user):
            return True
        if is_manager(user):
            # manager can manage tasks for their department or tasks they created/assigned
            if obj.department_id and user.department_id == obj.department_id:
                return True
            if obj.creator_id == user.id:
                return True
            if getattr(obj, "assigned_by_id", None) == user.id:
                return True
        # assignees can update limited fields (handled at serializer/view level)
        return obj.assignees.filter(id=user.id).exists()
