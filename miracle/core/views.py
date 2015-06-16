from django.contrib.auth.decorators import login_required
from json import dumps
from rest_framework import generics, renderers, permissions, views
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer
from .permissions import CanEditProject

import logging

logger = logging.getLogger(__name__)


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class ProjectListView(views.APIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    template_name = 'project/list.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, CanEditProject)

    def get(self, request, format=None):
        projects = Project.objects.viewable(request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response({'project_list_json': dumps(serializer.data)})


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    template_name = 'project/detail.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
