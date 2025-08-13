from rest_framework import permissions

class IsCEO(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CEO'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role.lower() == 'manager'

class IsHR(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'HR'

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Employee'

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Assumes the model instance has an `employee` attribute.
    """
    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user

class AnyOf(permissions.BasePermission):
    """
    Custom permission to allow access if any of the provided permissions are granted.
    """
    def __init__(self, *perms):
        self.perms = [perm() for perm in perms]

    def has_permission(self, request, view):
        return any(perm.has_permission(request, view) for perm in self.perms)

    def has_object_permission(self, request, view, obj):
        return any(getattr(perm, 'has_object_permission', lambda r, v, o: perm.has_permission(r, v))(request, view, obj) for perm in self.perms)
 
class IsManagerOfDepartment(permissions.BasePermission):
    """
    Allows access if the user is a manager and the object's department matches user's department.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and
            request.user.role == 'Manager' and
            hasattr(obj, 'department') and
            obj.department == request.user.department
        )
