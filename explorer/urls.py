"""
Defines the project-wide URL structure.

For more information, see
https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^explorer/', include('bdr.frontend.urls', namespace='bdr.frontend')),
    url(r'^backend/', include('bdr.backend.urls', namespace='bdr.backend')),
)
