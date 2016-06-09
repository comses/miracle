from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    # Examples:
    # url(r'^$', 'miracle.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('social.apps.django_app.urls', namespace='social')),
    url(r'^account/login/$', auth_views.login, {'template_name': 'account/login.html'}, name='login'),
    url(r'^account/logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),
    url(r'^account/password-reset/$', auth_views.password_reset,
        {'template_name': 'account/password-reset.html'}, name='password_reset'),
    url(r'^account/password-reset-confirm/$', auth_views.password_reset_confirm,
        {'template_name': 'account/password-reset-confirm.html'}, name='password_reset_confirm'),
    url(r'^account/password-reset-done/$', auth_views.password_reset_done,
        {'template_name': 'account/password-reset-done.html'}, name='password_reset_done'),
    url(r'^account/password-reset-complete/$', auth_views.password_reset_complete,
        {'template_name': 'account/password-reset-complete.html'}, name='password_reset_complete'),
    # django-contrib-comments URLs
    url(r'^comments/', include('django_comments.urls')),
    # fallback, core.urls will catch all other unmatched urls
    url(r'', include('miracle.core.urls', namespace='core', app_name='core')),
]
