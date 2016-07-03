from celery.result import AsyncResult
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from extra_views import InlineFormSet, UpdateWithInlinesView
from json import dumps, loads
from rest_framework import renderers, viewsets, generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.decorators import detail_route


from .models import (Project, ActivityLog, MiracleUser, DataTableGroup, DataAnalysisScript, AnalysisOutput, DataColumn,
                     AnalysisOutputFile)
from .serializers import (ProjectSerializer, DataFileSerializer, UserSerializer, DataTableGroupSerializer,
                          DataAnalysisScriptSerializer, AnalysisOutputSerializer, DataColumnSerializer,
                          ActivityLogSerializer,
                          )
from .permissions import (CanViewReadOnlyOrEditProject, CanViewReadOnlyOrEditProjectResource, )
from .tasks import run_analysis_task, run_metadata_pipeline

import logging
from os import path

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
        user = self.request.user
        project_serializer = ProjectSerializer(Project.objects.viewable(user), many=True,
                                               context={'request': self.request})
        # FIXME: won't scale for many users, change to client lookup
        user_serializer = UserSerializer(User.objects.all(), many=True)
        activity_serializer = ActivityLogSerializer(ActivityLog.objects.for_user(user), many=True)
        context.update(
            activity_log_json=dumps(activity_serializer.data),
            project_list_json=dumps(project_serializer.data),
            users_json=dumps(user_serializer.data),
        )
        return context


class SurveyView(LoginRequiredMixin, TemplateView):
    template_name = 'survey.html'

    def get_context_data(self, **kwargs):
        context = super(SurveyView, self).get_context_data(**kwargs)
        username = self.request.user.username
        context.update(
            surveyUrl="https://asu.co1.qualtrics.com/SE/?SID=SV_bpCMBE5PHiB9NaZ&UserName={0}".format(username)
        )
        return context


class UserActivityView(generics.GenericAPIView):
    renderer_classes = (renderers.JSONRenderer,)
    # FIXME: need to revisit permissions
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, username=None):
        activity_logs = ActivityLog.objects.filter(creator__username=username)
        serializer = ActivityLogSerializer(activity_logs, many=True)
        return Response(serializer.data, status=200)


class MiracleUserInline(InlineFormSet):
    model = MiracleUser
    can_delete = False
    fields = ('institution', 'user',)

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
                logger.exception("raised error")
                data.update(error_message=str(result))
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
        pk = int(query_params.get('pk'))
        parameters = loads(query_params.get('parameters'))
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

    @detail_route(methods=['get'])
    def download(self, request, pk):
        output = AnalysisOutputFile.objects.get(pk=pk)
        response = HttpResponse(output.output_file.file, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(output.basename)
        return response


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = DataAnalysisScriptSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)

    def get_queryset(self):
        # FIXME: replace with viewable QuerySet
        return DataAnalysisScript.objects.all()

    @property
    def template_name(self):
        return 'analysis/{}.html'.format(self.action)

    @detail_route(methods=['GET'])
    def download(self, request, pk):
        analysis = DataAnalysisScript.objects.get(id=pk)
        content = analysis.archived_file_contents()
        response = HttpResponse(content, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(analysis.basename)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super(AnalysisViewSet, self).retrieve(request, *args, **kwargs)
        analysis = self.get_object()
        if request.accepted_renderer.format == 'html':
            code = analysis.archived_file_contents_highlighted()
            response.data = {
                'code': code,
                'analysis': analysis
            }
        else:
            analysis_json = DataAnalysisScriptSerializer(analysis, context={'request': request})
            response.data = analysis_json.data
        return response


class DataColumnViewSet(viewsets.ModelViewSet):
    serializer_class = DataColumnSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)
    queryset = DataColumn.objects.all()

    def perform_update(self, serializer):
        data_column = serializer.save()
# FIXME: add modified data text to DataColumnSerializer?
        ActivityLog.objects.log_project_update(self.request.user, data_column.project,
                                               "Modified column {0}".format(data_column))


class DataTableGroupViewSet(viewsets.ModelViewSet):
    serializer_class = DataTableGroupSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProjectResource,)

    @property
    def template_name(self):
        return 'data-group/{}.html'.format(self.action)

    def retrieve(self, request, *args, **kwargs):
        response = super(DataTableGroupViewSet, self).retrieve(request, *args, **kwargs)
        data_group = response.data
        response.data['data_group_json'] = dumps(data_group)
        return response

    def get_queryset(self):
        return DataTableGroup.objects.viewable(self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    """ Provides viewset functionality for Projects """
    serializer_class = ProjectSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProject,)
    lookup_field = 'slug'

    @property
    def template_name(self):
        return 'project/{}.html'.format(self.action)

    def get_queryset(self):
        return Project.objects.viewable(self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.save(creator=user)
        ActivityLog.objects.log_project_update(user, project, "created")

    def retrieve(self, request, *args, **kwargs):
        response = super(ProjectViewSet, self).retrieve(request, *args, **kwargs)
        user_serializer = UserSerializer(User.objects.all(), many=True)
        project_data = response.data
        project = self.get_object()
        dependencies = project.package_dependencies()
        response.data = {
            'project_json': dumps(project_data),
            'users_json': dumps(user_serializer.data),
            'dependencies': dependencies,
            'radiant_url': settings.RADIANT_URL
        }
        if request.accepted_renderer.format == 'html':
            response.data['project'] = self.get_object()
        return response

    def perform_update(self, serializer):
        user = self.request.user
        project = serializer.save(user=user)
        logger.debug("UPDATE modified data: %s", serializer.modified_data)
        if serializer.modified_data:
            modified_data_text = serializer.modified_data_text
            logger.debug("modified data: %s", modified_data_text)
            ActivityLog.objects.log_project_update(user, project, modified_data_text)

    def perform_destroy(self, instance):
        instance.deactivate(self.request.user)

    @detail_route(methods=['get'])
    def download_archive(self, request, slug=None):
        project = self.get_object()
        logger.debug("getting project %s with slug %s", project, slug)
        archive_file = project.submitted_archive.file
        response = HttpResponse(archive_file, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(path.basename(archive_file.name))
        return response

    @detail_route(methods=['delete'])
    def clear_archive(self, request, slug=None):
        """ Deletes project archive directory and related entities"""
        project = self.get_object()
        user = request.user
        # FIXME: replace this with DRF permissions
        if project.has_admin_privileges(user):
            logger.debug("Resetting project archive for %s", project)
            project.clear_archive(user)
            return Response({'success': True, 'project': dumps(ProjectSerializer(project).data)})
        else:
            return Response({
                'success': False,
                'message': _('You must be a project admin in order to reset this project')
            })


class DataFileViewSet(viewsets.ModelViewSet):
    serializer_class = DataFileSerializer
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (CanViewReadOnlyOrEditProject,)


class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = (CanViewReadOnlyOrEditProject,)

    def post(self, request):
        file_obj = request.FILES['file']
        project_id = request.data.get('id')
        project = get_object_or_404(Project, pk=project_id)
        project.archive(file_obj)
        # should analyze payload
        task = run_metadata_pipeline.delay(project, project.archive_path)
        response = Response(data=task.id, status=status.HTTP_202_ACCEPTED)
        return response


class FileUploadStatusView(APIView):
    permission_classes = (CanViewReadOnlyOrEditProject,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, task_uuid):
        result = AsyncResult(task_uuid)
        if result.ready():
            if result.status == 'SUCCESS':
                sc = status.HTTP_201_CREATED
            elif result.status == 'FAILURE':
                # TODO: add error data
                sc = status.HTTP_400_BAD_REQUEST
            else:
                sc = status.HTTP_202_ACCEPTED

            return Response(result.status, status=sc)
        else:
            return Response(result.status, status=status.HTTP_202_ACCEPTED)


class FileUploadRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    permission_classes = (CanViewReadOnlyOrEditProject,)
    serializer_class = DataTableGroupSerializer
