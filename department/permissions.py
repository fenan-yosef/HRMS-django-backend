from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCEOOrReadOnly(BasePermission):
    """
    Only CEO can add, edit, or delete departments. Others can only view.
    """
    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return True
        return hasattr(user, 'role') and str(user.role).lower() == 'ceo'
