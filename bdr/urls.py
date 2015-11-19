"""
Defines the URL structure for the Biological Data Repository Web application.

For more information, see
https://docs.djangoproject.com/en/1.6/topics/http/urls/
"""

from django.conf.urls import include, patterns, url

from views import HomeView, SearchView, AboutView, LegalView, search_script
from views.categories import (CategoryListView, CategoryDetailView, CategoryAddView,
                              CategoryEditView, CategoryDeleteView)
from views.datasets import (DatasetListView, DatasetDetailView, DatasetAddView, DatasetEditView,
                            DatasetDeleteView)
from views.files import FileListView, FileDetailView, FileUploadView, FileEditView, FileDeleteView
from views.filters import FilterAddView, FilterEditView, FilterDeleteView
from views.formats import FormatListView, dispatch as dispatch_format_view
from views.revisions import (RevisionDetailView, RevisionEditView, RevisionDeleteView, LatestRevisionRedirectView,
                             dispatch as dispatch_export_view)
from views.sources import (SourceListView, SourceDetailView, SourceAddView, SourceEditView,
                           SourceDeleteView)
from views.tags import TagListView, TagDetailView, TagAddView, TagEditView, TagDeleteView

__all__ = []
__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Biological Dataset Repository: data archival and retrieval.
    Copyright (C) 2015  Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
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
        url(r'^files/$', FileListView.as_view(), name='files'),
        url(r'^files/upload$', FileUploadView.as_view(), name='upload-file'),
        url(r'^files/(?P<filename>[\w_-]+)-(?P<fpk>\d+)/', include(patterns(
            '',
            url(r'^view$', FileDetailView.as_view(), name='view-file'),
            url(r'^edit$', FileEditView.as_view(), name='edit-file'),
            url(r'^delete$', FileDeleteView.as_view(), name='delete-file'),


            # Revisions
            # TODO: Implement revision views
            # url(r'^revisions/upload$', RevisionUploadView.as_view(), name='upload-revision'),
            url(r'^revisions/(?P<revision>\d+)-(?P<rpk>\d+)/', include(patterns(
                '',
                url(r'^view$', RevisionDetailView.as_view(), name='view-revision'),
                url(r'^edit$', RevisionEditView.as_view(), name='edit-revision'),
                url(r'^delete$', RevisionDeleteView.as_view(), name='delete-revision'),
                url(r'^export$', dispatch_export_view, {'view': 'export'}, name='export-revision'),
            ))),
            url(r'^revisions/latest/', include(patterns(
                '',
                url(r'^view$', LatestRevisionRedirectView.as_view(), dict(path='view'),
                    name='view-latest-revision'),
                url(r'^edit$', LatestRevisionRedirectView.as_view(), dict(path='edit'),
                    name='edit-latest-revision'),
                url(r'^delete$', LatestRevisionRedirectView.as_view(), dict(path='delete'),
                    name='delete-latest-revision'),
                url(r'^export$', LatestRevisionRedirectView.as_view(), dict(path='export'),
                    name='export-latest-revision'),
            ))),
        ))),


        # Sources
        url(r'^sources/$', SourceListView.as_view(), name='sources'),
        url(r'^sources/add$', SourceAddView.as_view(), name='add-source'),
        url(r'^sources/(?P<source>\d+)/', include(patterns(
            '',
            url(r'^view$', SourceDetailView.as_view(), name='view-source'),
            url(r'^edit$', SourceEditView.as_view(), name='edit-source'),
            url(r'^delete$', SourceDeleteView.as_view(), name='delete-source'),


            # Filters
            url(r'^filters/add$', FilterAddView.as_view(), name='add-filter'),
            url(r'^filters/(?P<filter>\d+)/', include(patterns(
                '',
                url(r'^edit$', FilterEditView.as_view(), name='edit-filter'),
                url(r'^delete$', FilterDeleteView.as_view(), name='delete-filter'),
            )))
        ))),
    ))),


    # Formats
    url(r'^formats/$', FormatListView.as_view(), name='formats'),
    url(r'^formats/create/(?P<type>[\w-]+)$', dispatch_format_view, {"view": "create"}, name='create-format'),
    url(r'^formats/(?P<pk>\d+)/', include(patterns(
        '',
        url(r'^view$', dispatch_format_view, {"view": "view"}, name='view-format'),
        url(r'^edit$', dispatch_format_view, {"view": "edit"}, name='edit-format'),
        url(r'^delete$', dispatch_format_view, {"view": "delete"}, name='delete-format'),
    ))),
)
