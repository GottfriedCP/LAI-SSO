from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow edit object if owner, else read only.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions to Safe Method (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to owner of the obj
        # 'owner' from Model
        return obj.owner == request.user
