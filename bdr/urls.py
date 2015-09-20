"""
Defines the URL structure for the Biological Data Repository Web application.

For more information, see
https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import include, patterns, url

from bdr.frontend.views import formats, revisions

from views import HomeView, SearchView, AboutView, LegalView, search_script
from views.categories import (CategoryListView, CategoryDetailView, CategoryAddView,
                              CategoryEditView, CategoryDeleteView)
from views.datasets import (DatasetListView, DatasetDetailView, DatasetAddView, DatasetEditView,
                            DatasetDeleteView)
from views.files import FileDetailView, FileUploadView, FileEditView, FileDeleteView
from views.tags import TagListView, TagDetailView, TagAddView, TagEditView, TagDeleteView

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
    url(r'^search$', SearchView.as_view(), name='search'),

    url(r'^js/search.js$', search_script, name='search.js'),

    # Categories
    url(r'^categories/$', CategoryListView.as_view(), name='categories'),
    url(r'^categories/add$', CategoryAddView.as_view(), name='add-category'),
    url(r'^categories/(?P<name>[\w_-]+)-(?P<pk>\d+)/', include(patterns(
        '',
        url(r'^view$', CategoryDetailView.as_view(), name='view-category'),
        url(r'^edit$', CategoryEditView.as_view(), name='edit-category'),
        url(r'^delete$', CategoryDeleteView.as_view(), name='delete-category'),
    ))),

    # Tags
    url(r'^tags/$', TagListView.as_view(), name='tags'),
    url(r'^tags/add$', TagAddView.as_view(), name='add-tag'),
    url(r'^tags/(?P<name>[\w_-]+)-(?P<pk>\d+)/', include(patterns(
        '',
        url(r'^view$', TagDetailView.as_view(), name='view-tag'),
        url(r'^edit$', TagEditView.as_view(), name='edit-tag'),
        url(r'^delete$', TagDeleteView.as_view(), name='delete-tag'),
    ))),


    # Datasets
    url(r'^datasets/$', DatasetListView.as_view(), name='datasets'),
    url(r'^datasets/add$', DatasetAddView.as_view(), name='add-dataset'),
    url(r'^datasets/(?P<dataset>[\w_-]+)-(?P<dpk>\d+)/', include(patterns(
        '',
        url(r'^view$', DatasetDetailView.as_view(), name='view-dataset'),
        url(r'^edit$', DatasetEditView.as_view(), name='edit-dataset'),
        url(r'^delete$', DatasetDeleteView.as_view(), name='delete-dataset'),


        # Files
        url(r'^files/upload$', FileUploadView.as_view(), name='upload-file'),
        url(r'^files/(?P<filename>[\w_-]+)-(?P<fpk>\d+)/', include(patterns(
            '',
            url(r'^view$', FileDetailView.as_view(), name='view-file'),
            url(r'^edit$', FileEditView.as_view(), name='edit-file'),
            url(r'^delete$', FileDeleteView.as_view(), name='delete-file'),


            # Revisions
            # TODO: Implement revision views
            # url(r'^revisions/upload$', RevisionUploadView.as_view(), name='upload-revision'),
            # url(r'^revisions/(?P<revision>\d+)-(?P<rpk>\d+)/', include(patterns(
            #     '',
            #     url(r'^view$', RevisionDetailView.as_view(), name='view-revision'),
            #     url(r'^edit$', RevisionEditView.as_view(), name='edit-revision'),
            #     url(r'^delete$', RevisionDeleteView.as_view(), name='delete-revision'),
            #     url(r'^export$', RevisionExportView.as_view(), name='export-revision'),
            # ))),
        ))),

    ))),

    url(r'^formats/$', formats.FormatListView.as_view(), name='formats'),
    url(r'^formats/add$', formats.FormatAddView.as_view(), name='format-add'),
    url(r'^formats/(?P<slug>[\w-]+)$', formats.FormatDetailView.as_view(), name='format-detail'),
    url(r'^formats/(?P<slug>[\w-]+)/edit$', formats.FormatEditView.as_view(), name='format-edit'),
    url(r'^formats/(?P<slug>[\w-]+)/delete$', formats.FormatDeleteView.as_view(), name='format-delete'),

    url(r'^datasets/(?P<ds>[\w-]+)/(?P<fn>[\w .()/-]+)/(?P<rev>(?:\d+|latest))$',
        revisions.RevisionDownloadView.as_view(),
        name='download'),
)
