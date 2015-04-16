from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    # Examples:
    # url(r'^$', 'miracle.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    # from . import metadata
    # url(r'^metadata/', include(metadata.urls)),

    url(r'^admin/', include(admin.site.urls)),
]
