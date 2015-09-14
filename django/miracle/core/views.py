from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from extra_views import InlineFormSet, UpdateWithInlinesView
from json import dumps
from rest_framework import renderers, viewsets, generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (Project, ActivityLog, MiracleUser, Dataset, Analysis)
from .serializers import (ProjectSerializer, UserSerializer, DatasetSerializer, AnalysisSerializer)
from .permissions import (CanViewReadOnlyOrEditProject, CanViewReadOnlyOrEditProjectResource, )
from .tasks import run_analysis_task


import logging

logger = logging.getLogger(__name__)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(*args, **kwargs)
        return login_required(view)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        project_serializer = ProjectSerializer(Project.objects.viewable(self.request.user), many=True,
                                               context={'request': self.request})
        user_serializer = UserSerializer(User.objects.all(), many=True)
        context.update(
            activity_log=ActivityLog.objects.for_user(self.request.user),
            project_list_json=dumps(project_serializer.data),
            users_json=dumps(user_serializer.data),
            request=self.request,
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


class RunAnalysisView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Issues a celery request to run this analysis and return a 202 status URL to poll for the status of this request.
        """
        query_params = request.query_params
        pk = query_params.get('pk')
        parameters = query_params.get('parameters')
        logger.debug("running analysis id %s with parameters %s", pk, parameters)
        task_id = run_analysis_task.delay(pk, parameters)
        return Response({'task_id': task_id}, status=202)


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)

    def get_queryset(self):
        # FIXME: replace with viewable QuerySet
        return Analysis.objects.all()

    @property
    def template_name(self):
        return 'analysis/{}.html'.format(self.action)


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)

    @property
    def template_name(self):
        return 'dataset/{}.html'.format(self.action)

    def get_queryset(self):
        return Dataset.objects.viewable(self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    """ Project controller """
    serializer_class = ProjectSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProject,)

    @property
    def template_name(self):
        return 'project/{}.html'.format(self.action)

    def get_queryset(self):
        return Project.objects.viewable(self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        response = super(ProjectViewSet, self).retrieve(request, *args, **kwargs)
        user_serializer = UserSerializer(User.objects.all(), many=True)
        project = response.data
        response.data = {
            'project': self.get_object(),
            'project_json': dumps(project),
            'users_json': dumps(user_serializer.data),
        }
        return response

    def perform_update(self, serializer):
        logger.debug("performing update with serializer: %s", serializer)
        user = self.request.user
        project = serializer.save(user=user)
        logger.debug("modified data: %s", serializer.modified_data_text)
        ActivityLog.objects.log_user(user, 'UPDATE {}: {}'.format(
            project,
            serializer.modified_data_text))

    def perform_destroy(self, instance):
        instance.deactivate(self.request.user)


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = (CanViewReadOnlyOrEditProject,)

    def post(self, request, format=None):
        file_obj = request.FILES['file']
        project = get_object_or_404(Project, pk=request.data.get('id'))
        user = request.user
# should analyze payload
        dataset = Dataset(name=file_obj.name, creator=user, project=project, uploaded_file=file_obj)
        dataset.save()
        return Response(status=201)


class FileUploadRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    permission_classes = (CanViewReadOnlyOrEditProject,)
    serializer_class = DatasetSerializer
