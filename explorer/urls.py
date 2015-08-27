"""
Defines the project-wide URL structure.

For more information, see https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('bdr.urls', namespace='bdr', app_name='bdr')),
    url(r'^explorer/', include('bdr.urls', namespace='bdr.frontend')),
    url(r'^backend/', include('bdr.backend.urls', namespace='bdr.backend')),
)
