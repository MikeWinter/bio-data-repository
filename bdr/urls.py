"""
Defines the URL structure for the Biological Data Repository Web application.

For more information, see
https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import patterns, url

from bdr.frontend import views as old_views
from bdr.frontend.views import files, formats, revisions, tags

from views import HomeView, AboutView, LegalView, search_script
from views.categories import (CategoryListView, CategoryDetailView, CategoryAddView,
                              CategoryEditView, CategoryDeleteView)
from views.datasets import (DatasetListView, DatasetDetailView, DatasetAddView,
                            DatasetEditView, DatasetDeleteView)

__all__ = []
__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Copyright (C) 2015 Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
    """

urlpatterns = patterns(
    '',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^about$', AboutView.as_view(), name='about'),
    url(r'^legal$', LegalView.as_view(), name='legal'),
    url(r'^search$', old_views.SearchView.as_view(), name='search'),

    url(r'^categories/$', CategoryListView.as_view(), name='categories'),
    url(r'^datasets/$', DatasetListView.as_view(), name='datasets'),
    url(r'^formats/$', formats.FormatListView.as_view(), name='formats'),
    url(r'^tags/$', tags.TagListView.as_view(), name='tags'),

    url(r'^categories/(?P<name>[\w_-]+)-(?P<pk>\d+)$', CategoryDetailView.as_view(),
        name='category'),
    url(r'^categories/add$', CategoryAddView.as_view(),
        name='add-category'),
    url(r'^categories/(?P<name>[\w_-]+)-(?P<pk>\d+)/edit$', CategoryEditView.as_view(),
        name='edit-category'),
    url(r'^categories/(?P<name>[\w_-]+)-(?P<pk>\d+)/delete$', CategoryDeleteView.as_view(),
        name='delete-category'),

    url(r'^datasets/(?P<name>[\w_-]+)-(?P<pk>\d+)$', DatasetDetailView.as_view(),
        name='dataset'),
    url(r'^datasets/add$', DatasetAddView.as_view(),
        name='add-dataset'),
    url(r'^datasets/(?P<name>[\w_-]+)-(?P<pk>\d+)/edit$', DatasetEditView.as_view(),
        name='edit-dataset'),
    url(r'^datasets/(?P<name>[\w_-]+)-(?P<pk>\d+)/delete$', DatasetDeleteView.as_view(),
        name='delete-dataset'),

    url(r'^formats/add$', formats.FormatAddView.as_view(), name='format-add'),
    url(r'^formats/(?P<slug>[\w-]+)$', formats.FormatDetailView.as_view(), name='format-detail'),
    url(r'^formats/(?P<slug>[\w-]+)/edit$', formats.FormatEditView.as_view(), name='format-edit'),
    url(r'^formats/(?P<slug>[\w-]+)/delete$', formats.FormatDeleteView.as_view(), name='format-delete'),

    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/(?P<rev>(?:\d+|latest))$',
        revisions.RevisionDownloadView.as_view(),
        name='download'),

    url(r'^datasets/(?P<slug>[\w-]+)/add$', files.FileAddView.as_view(), name='file-add'),
    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/$', files.FileDetailView.as_view(), name='file-detail'),

    url(r'^tags/add$', tags.TagAddView.as_view(), name='tag-add'),
    url(r'^tags/(?P<name>[\w-]+)$', tags.TagDetailView.as_view(), name='tag-detail'),
    url(r'^tags/(?P<name>[\w-]+)/edit$', tags.TagEditView.as_view(), name='tag-edit'),
    url(r'^tags/(?P<name>[\w-]+)/delete$', tags.TagDeleteView.as_view(), name='tag-delete'),

    url(r'^js/search.js$', search_script, name='search.js'),
)
