"""
This module defines classes for displaying and editing datasets.
"""

from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..models import Dataset

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


class DatasetDetailView(SearchableViewMixin, SingleObjectMixin, ListView):
    """
    This view displays the details of a dataset, including a list of its files
    and links to the most recent revision of each file.
    """

    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/datasets/dataset_detail.html"

    def __init__(self, **kwargs):
        super(DatasetDetailView, self).__init__(**kwargs)
        self.object = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=Dataset.objects.all())
        return super(DatasetDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DatasetDetailView, self).get_context_data(**kwargs)
        context["dataset"] = self.object
        return context

    def get_queryset(self):
        return self.object.files.all()


class DatasetListView(SearchableViewMixin, ListView):
    """This view displays a list of datasets stored in the repository."""

    model = Dataset
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/datasets/dataset_list.html"
    context_object_name = "datasets"
