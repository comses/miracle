from rest_framework import permissions

import logging

logger = logging.getLogger(__name__)


class CanEditProject(permissions.BasePermission):

    def has_permission(self, request, view):
        logger.debug("checking if user %s can issue %s against %s", request.user, request, view)
        return request.user.is_authenticated()

    def has_object_permission(self, request, view, project):
        user = request.user
        if user.is_superuser:
            return True
        logger.debug("checking user %s against project %s", user, project)
        return user.is_authenticated() and project.creator == user or project.has_group_member(user)
