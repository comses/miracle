from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    # Examples:
    # url(r'^$', 'miracle.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('social.apps.django_app.urls', namespace='social')),
    # need to change this
    #url(r'^login/$', 'django.contrib.auth.views.login'),
    url(r'', include('django.contrib.auth.urls')),
    # fallback, core.urls will catch all other unmatched urls
    url(r'', include('miracle.core.urls', namespace='core', app_name='core')),
]

# add user uploaded files to handled urlpatterns in development mode.
# NOTE: never allow this in production, see
# https://docs.djangoproject.com/en/1.8/howto/static-files/#serving-uploaded-files-in-development for more details
# otherwise this can be a security risk.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
