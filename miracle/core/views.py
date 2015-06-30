from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView
from extra_views import InlineFormSet, UpdateWithInlinesView
from json import dumps
from rest_framework import generics, renderers, permissions

from .models import Project, ActivityLog, MiracleUser
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


class MiracleUserInline(InlineFormSet):
    model = MiracleUser
    can_delete = False

    def get_object(self):
        return MiracleUser.objects.get(user=self.request.user)


class UserProfileView(LoginRequiredMixin, UpdateWithInlinesView):
    template_name = 'account/profile.html'
    model = User
    inlines = [MiracleUserInline]
    fields = ('username', 'first_name', 'last_name', 'email')
    success_url = reverse_lazy('core:profile')

    def get_object(self):
        return self.request.user


class ProjectListView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    template_name = 'project/list.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        return Project.objects.viewable(self.request.user)

    def get(self, request, *args, **kwargs):
        response = super(ProjectListView, self).get(request, *args, **kwargs)
        original_response_data = response.data
        response.data = {'project_list_json': dumps(original_response_data)}
        return response

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.save(creator=user)
        ActivityLog.objects.log_user(user, 'Created project {}'.format(project))


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    template_name = 'project/detail.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanEditProject,)

    def get(self, request, *args, **kwargs):
        response = super(ProjectDetailView, self).get(request, *args, **kwargs)
        original_response_data = response.data
        response.data = {'project': self.get_object(), 'project_json': dumps(original_response_data)}
        return response

    def perform_update(self, serializer):
        project = serializer.save()
        ActivityLog.objects.log_user(self.request.user, 'Updating project {} with serializer {}'.format(
            project,
            serializer.errors))

    def perform_destroy(self, instance):
        instance.deactivate(self.request.user)
