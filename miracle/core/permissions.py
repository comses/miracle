from rest_framework import permissions

class CanEditProject(permissions.BasePermission):

    def has_object_permission(self, request, view, project):
        # allow GET / HEAD / OPTIONS for all, revisit and revoke if needed
        if request.method in permissions.SAFE_METHODS:
            return True
        requesting_user = request.user
        return project.creator == requesting_user or project.has_group_member(requesting_user)
