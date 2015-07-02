from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView
from extra_views import InlineFormSet, UpdateWithInlinesView
from json import dumps
from rest_framework import renderers, viewsets, mixins, status
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


class ProjectViewSet(mixins.UpdateModelMixin,
                     # mixins.CreateModelMixin,
                     # mixins.ListModelMixin,
                     viewsets.GenericViewSet):
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

    def create(self, request, *args, **kwargs):
        logger.debug("WHAT")
        serializer = self.get_serializer(data=request.data)
        logger.debug("getting serializer %s for data %s", serializer, request.data)
        serializer.is_valid(raise_exception=True)
        headers = self.get_success_headers(serializer.data)
        instance = serializer.save()
        logger.debug("created instance %s with serializer: %s", instance, serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        # FIXME: use ListModelMixin if pagination needed
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({
            'project_list_json': dumps(serializer.data)
        })

    def retrieve(self, request, pk=None):
        project = self.get_object()
        serializer = self.get_serializer(project)
        return Response({
            'project': project,
            'project_json': dumps(serializer.data),
        })

    def perform_update(self, serializer):
        user = self.request.user
        project = serializer.save(user=user)
        logger.debug("modified data: %s", serializer.modified_data_text)
        ActivityLog.objects.log_user(user, 'Updating project {} with serializer {}'.format(
            project,
            serializer.modified_data_text))
