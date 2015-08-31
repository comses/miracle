from rest_framework import permissions

import logging

logger = logging.getLogger(__name__)


class CanViewReadOnlyOrEditProject(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, project):
        user = request.user
        return (
            user.is_superuser or
            (project.published and request.method in permissions.SAFE_METHODS) or
            (user.is_authenticated() and project.has_group_member(user))
        )


class CanViewReadOnlyOrEditDatasetProject(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, dataset):
        user = request.user
        return (
            user.is_superuser or
            (dataset.published and request.method in permissions.SAFE_METHODS) or
            (user.is_authenticated() and dataset.project.has_group_member(user))
        )
