from django.conf.urls import url
from django.views.generic import TemplateView, RedirectView


urlpatterns = [
    # Examples:
    # url(r'^$', 'miracle.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    # FIXME: replace these with forms if needed
    url(r'^contact$', RedirectView.as_view(url='https://groups.google.com/forum/#!forum/comses-dev'), name='contact'),
    url(r'^report-bug$', RedirectView.as_view(url='https://github.com/comses/miracle/issues/new'), name='report_bug'),

]
