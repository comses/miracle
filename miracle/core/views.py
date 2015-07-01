from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from extra_views import InlineFormSet, UpdateWithInlinesView
from json import dumps
from rest_framework import renderers, viewsets
from rest_framework.response import Response

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


class ProjectViewSet(viewsets.ModelViewSet):
    """ Project controller """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanEditProject,)

    @property
    def template_filename(self):
        _action = self.action
        if _action == 'retrieve':
            _action = 'detail'
        return '{}.html'.format(_action)

    @property
    def template_name(self):
        return 'project/{}'.format(self.template_filename)

    def get_queryset(self):
        return Project.objects.viewable(self.request.user)

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({
            'project_list_json': dumps(serializer.data)
        })

    def retrieve(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)
        serializer = self.get_serializer(project)
        return Response({
            'project': project,
            'project_json': dumps(serializer.data),
        })

    def update(self, request, pk=None):
        project = get_object_or_404(Project, pk=pk)
        serializer = self.get_serializer(project, request.data)
        logger.debug("serializer: %s", serializer)
        if serializer.is_valid():
            project = serializer.save(user=self.request.user)
            ActivityLog.objects.log_user(self.request.user, 'Updating project {} with serializer {}'.format(
                project,
                serializer))
            return Response(serializer.data)
        else:
            logger.debug("serializer invalid, errors: %s", serializer.errors)
            return Response(serializer.errors)
