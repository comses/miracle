from celery.result import AsyncResult
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

from .models import (Project, ActivityLog, MiracleUser, Dataset, Analysis, AnalysisOutput)
from .serializers import (ProjectSerializer, ProjectPathSerializer, UserSerializer, DatasetSerializer, AnalysisSerializer,
                          AnalysisOutputSerializer)
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


class CheckAnalysisRunStatusView(APIView):
    renderer_classes = (renderers.JSONRenderer,)
    # FIXME: need to revisit permissions
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params
        task_id = query_params.get('task_id')
        async_result = AsyncResult(task_id)
        data = {'ready': async_result.ready(), 'status': async_result.status}
        if async_result.ready():
            result = async_result.result
            if isinstance(result, Exception):
                logger.debug("raised error")
                data.update(error_message=unicode(result))
            else:
# run succeeded, serialize the result
                logger.debug("async result output: type(%s) - %s", type(result), result)
                serializer = AnalysisOutputSerializer(result)
                data.update(output=serializer.data)
        # query celery task status
        return Response(data, status=200)


class ShareOutputView(APIView):
    renderer_classes = (renderers.JSONRenderer,)
    # FIXME: revisit permissions
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        output_id = request.data.get('id')
        email = request.data.get('email')
        message = request.data.get('message')
        logger.debug("user %s sharing output %s with [%s]: %s", user, output_id, email, message)
        return Response(status=200)


class RunAnalysisView(APIView):
    renderer_classes = (renderers.JSONRenderer,)
    # FIXME: revisit permissions
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Issues a celery request to run this analysis and return a 202 status URL to poll for the status of this request.
        """
        query_params = request.query_params
        pk = query_params.get('pk')
        parameters = query_params.get('parameters')
        logger.debug("running analysis id %s with parameters %s", pk, parameters)
        async_result = run_analysis_task.delay(pk, parameters, user=request.user)
        logger.debug("running analysis task with id %s", async_result.id)
        return Response({'task_id': async_result.id}, status=202)


class OutputViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisOutputSerializer
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)

    def get_queryset(self):
        # FIXME: replace with viewable QuerySet
        return AnalysisOutput.objects.all()

    @property
    def template_name(self):
        return 'output/{}.html'.format(self.action)


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
            'project_json': dumps(project),
            'users_json': dumps(user_serializer.data),
        }
        if request.accepted_renderer.format == 'html':
            response.data['project'] = self.get_object()
        return response

    def perform_update(self, serializer):
        user = self.request.user
        project = serializer.save(user=user)
        logger.debug("modified data: %s", serializer.modified_data_text)
        ActivityLog.objects.log_user(user, 'UPDATE {}: {}'.format(
            project,
            serializer.modified_data_text))

    def perform_destroy(self, instance):
        instance.deactivate(self.request.user)

class ProjectPathViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectPathSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProject,)

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = (CanViewReadOnlyOrEditProject,)

    def post(self, request, format=None):
        file_obj = request.FILES['file']
        project = get_object_or_404(Project, pk=request.data.get('id'))
        user = request.user
# should analyze payload
        dataset = Dataset(name=file_obj.name, creator=user, project=project, path=file_obj)
        dataset.save()
        return Response(status=201)


class FileUploadRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    permission_classes = (CanViewReadOnlyOrEditProject,)
    serializer_class = DatasetSerializer
