# hr_system/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to edit an object.
    Non-admin users have read-only access.
    We assume an 'is_admin' or 'is_staff' flag on the user model.
    """
    def has_permission(self, request, view):
        # Allow all GET, HEAD, or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to admin users.
        # Django's 'is_staff' is a good proxy for an HR admin in this context.
        return request.user and request.user.is_staff

class IsManagerAndOwnerOrReadOnly(BasePermission):
    """
    Permission for objects related to an employee.
    Allows managers to view their team's data, and employees to view their own.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user for now,
        # but we'll check if they are the owner or manager.
        if request.method in SAFE_METHODS:
            # Check if the user is the employee themselves, or their manager
            return obj.employee == request.user.employee or obj.employee.manager == request.user.employee
        
        # Write permissions are only allowed to the owner of the object.
        return obj.employee == request.user.employee

class IsEmployeeOwner(BasePermission):
    """
    Allows users to view any profile (for company directory), but only edit their own.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user (e.g., for a company directory)
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the user themselves.
        # This assumes a OneToOneField from User to Employee named 'employee'
        return obj == request.user.employee

