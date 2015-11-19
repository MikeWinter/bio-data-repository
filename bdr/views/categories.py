"""
This module defines classes for displaying and editing categories.
"""

from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..forms import CategoryForm
from ..models import Category

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


class CategoryDetailView(SearchableViewMixin, SingleObjectMixin, ListView):
    """Displays a detailed view of a given category."""

    model = Category
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/categories/category_detail.html"

    def __init__(self, **kwargs):
        super(CategoryDetailView, self).__init__(**kwargs)
        self.object = None

    def get(self, request, *args, **kwargs):
        """
        Send a response for HTTP GET requests sent to this view.

        :param request: The request received by the view.
        :type request: django.http.HttpRequest
        :param args: The positional arguments captured from the route for this
                     view.
        :param kwargs: The named arguments captured from the route for this
                       view.
        :return: The response.
        :rtype: django.http.HttpResponseBase
        """
        self.object = self.get_object(queryset=self.model.objects.all())
        return super(CategoryDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``category`` - this category
         * ``datasets`` - the datasets associated with this category

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        context["datasets"] = context["object_list"]
        return context

    def get_queryset(self):
        """
        Get the list of datasets associated with this category.

        :return: The datasets associated with this category.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return self.object.datasets.all()


class CategoryListView(SearchableViewMixin, ListView):
    """Lists categories previously added to the repository."""

    context_object_name = "categories"
    model = Category
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/categories/category_list.html"


class CategoryEditView(SearchableViewMixin, UpdateView):
    """Edits existing categories."""

    model = Category
    form_class = CategoryForm
    template_name = "bdr/categories/category_edit.html"


class CategoryDeleteView(SearchableViewMixin, DeleteView):
    """Deletes an existing category."""

    model = Category
    success_url = reverse_lazy('bdr:categories')
    template_name = "bdr/categories/category_confirm_delete.html"


class CategoryAddView(SearchableViewMixin, CreateView):
    """Creates a new category."""

    model = Category
    form_class = CategoryForm
    template_name = "bdr/categories/category_add.html"
