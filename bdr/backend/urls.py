"""
Defines the URL structure for the back-end web server application.

For more information, see
https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import patterns, url

from bdr.backend import views


urlpatterns = patterns(
    '',
    url(r'^categories/$', views.CategoryCollectionView.as_view(), name='categories'),
    url(r'^datasets/$', views.DatasetCollectionView.as_view(), name='datasets'),
    url(r'^files/$', views.FileCollectionView.as_view(), name='files'),
    url(r'^formats/$', views.FormatCollectionView.as_view(), name='formats'),
    url(r'^revisions/$', views.RevisionCollectionView.as_view(), name='revisions'),
    url(r'^tags/$', views.TagCollectionView.as_view(), name='tags'),

    url(r'^categories/(?P<slug>[\w-]+)$', views.CategoryDetailView.as_view(), name='category-detail'),

    url(r'^datasets/(?P<slug>[\w-]+)$', views.DatasetDetailView.as_view(), name='dataset-detail'),
    url(r'^datasets/(?P<ds>[\w-]+)/$', views.DatasetFilesCollectionView.as_view(), name='dataset-files'),

    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/(?P<rev>\d+)$', views.RevisionDetailView.as_view(),
        name='revision-detail'),
    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/(?P<rev>\d+)/data$', views.ExportView.as_view(), name='export'),

    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]*[\w .()-])$', views.FileDetailView.as_view(), name='file-detail'),
    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/$', views.FileRevisionsCollectionView.as_view(),
        name='file-revisions'),

    url(r'^formats/(?P<slug>[\w-]+)$', views.FormatDetailView.as_view(), name='format-detail'),

    url(r'^tags/(?P<pk>\d+)$', views.TagDetailView.as_view(), name='tag-detail'),
)
