from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView

from rest_framework import routers

from . import views


urlpatterns = [
    # Examples:
    # url(r'^$', 'miracle.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    # FIXME: replace these with forms if needed
    url(r'^contact/$', RedirectView.as_view(url='https://groups.google.com/forum/#!forum/comses-dev', permanent=False),
        name='contact'),
    url(r'^report-bug/$', RedirectView.as_view(url='https://github.com/comses/miracle/issues/new', permanent=False),
        name='report_bug'),
    url(r'^dashboard/$', views.DashboardView.as_view(), name='dashboard'),

    url(r'^search/$', TemplateView.as_view(template_name='search.html'), name='search'),
    # FIXME: consider merging these one-off /analysis endpoints into a single endpoint with an action parameter
    url(r'^analysis/run/$', views.RunAnalysisView.as_view(), name='run-analysis'),
    url(r'^analysis/run/status/$', views.CheckAnalysisRunStatusView.as_view(), name='check-analysis-run-status'),
    url(r'^analysis/output/share/$', views.ShareOutputView.as_view(), name='share-output'),
    url(r'^user/(?P<username>[\w.@+-]+)/activity/$', views.UserActivityView.as_view(), name='user-activity'),
    url(r'^account/profile/$', views.UserProfileView.as_view(), name='profile'),
    url(r'^projects/upload/$', views.FileUploadView.as_view(), name='upload'),
    url(r'^projects/upload/(?P<task_uuid>[0-9\-a-f]+)/$', views.FileUploadStatusView.as_view(), name='upload-status'),
    url(r'^survey/$', views.SurveyView.as_view(), name='survey'),
]

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet, base_name='project')
router.register(r'data-group', views.DataTableGroupViewSet, base_name='data-group')
router.register(r'data-column', views.DataColumnViewSet, base_name='data-column')
router.register(r'analyses', views.AnalysisViewSet, base_name='analysis')
router.register(r'outputs', views.OutputViewSet, base_name='output')
urlpatterns += router.urls
