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
    url(r'^contact/$', RedirectView.as_view(url='https://_groups.google.com/forum/#!forum/comses-dev', permanent=False),
        name='contact'),
    url(r'^report-bug/$', RedirectView.as_view(url='https://github.com/comses/miracle/issues/new', permanent=False),
        name='report_bug'),
    url(r'^dashboard/$', views.DashboardView.as_view(), name='dashboard'),
    url(r'^search/$', TemplateView.as_view(template_name='search.html'), name='search'),
    # FIXME: consider merging these one-off /analysis endpoints into a single endpoint with an action parameter
    url(r'^analysis/run/$', views.RunAnalysisView.as_view(), name='run-analysis'),
    url(r'^analysis/run/status/$', views.CheckAnalysisRunStatusView.as_view(), name='check-analysis-run-status'),
    url(r'^analysis/output/share/$', views.ShareOutputView.as_view(), name='share-output'),
    url(r'^account/profile/$', views.UserProfileView.as_view(), name='profile'),
    url(r'^file-upload/$', views.FileUploadView.as_view(), name='upload'),
    url(r'^file-upload-status/$', views.FileUploadStatusView.as_view(), name='upload-status')
]

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet, base_name='project')
router.register(r'datasets', views.DataTableGroupViewSet, base_name='dataset')
router.register(r'analyses', views.AnalysisViewSet, base_name='analysis')
router.register(r'outputs', views.OutputViewSet, base_name='output')
urlpatterns += router.urls
