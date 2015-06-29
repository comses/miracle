from rest_framework import permissions


class CanEditProject(permissions.BasePermission):

    def has_object_permission(self, request, view, project):
        requesting_user = request.user
        return project.creator == requesting_user or project.has_group_member(requesting_user)
