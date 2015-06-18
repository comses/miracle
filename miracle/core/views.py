from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from json import dumps
from rest_framework import generics, renderers, permissions
from rest_framework.response import Response

from .models import Project, ActivityLog
from .serializers import ProjectSerializer
from .permissions import CanEditProject

import logging

logger = logging.getLogger(__name__)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context.update(
            activity_log=ActivityLog.objects.for_user(self.request.user),
        )
        return context


class ProjectListView(generics.GenericAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    template_name = 'project/list.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, format=None):
        projects = Project.objects.viewable(request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response({'project_list_json': dumps(serializer.data)})


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    template_name = 'project/detail.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanEditProject,)

    def get(self, request, *args, **kwargs):
        response = super(ProjectDetailView, self).get(request, *args, **kwargs)
        original_response_data = response.data
        response.data = {'project_json': dumps(original_response_data)}
        return response

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.save(creator=user)
        ActivityLog.objects.log_user(user, 'Created project {}'.format(project))

    def perform_update(self, serializer):
        project = serializer.save()
        ActivityLog.objects.log_user(self.request.user,
                                     'Updating project {} with serializer {}'.format(
                                         project,
                                         serializer.errors))

    def perform_destroy(self, instance):
        instance.deactivate(self.request.user)
