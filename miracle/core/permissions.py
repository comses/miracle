from rest_framework import permissions

import logging

logger = logging.getLogger(__name__)


class CanEditProject(permissions.BasePermission):

    def has_object_permission(self, request, view, project):
        user = request.user
        return user.is_authenticated() and project.creator == user or project.has_group_member(user)
