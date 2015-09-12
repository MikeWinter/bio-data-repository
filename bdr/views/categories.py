"""
This module defines classes for displaying and editing categories.
"""

from django.core.urlresolvers import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView, DeleteView, CreateView

from . import SearchableViewMixin
from ..forms import CategoryForm
from ..models import Category

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


class CategoryDetailView(SearchableViewMixin, DetailView):
    """Displays a detailed view of a given category."""

    model = Category
    template_name = "bdr/categories/category_detail.html"


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


class CategoryAddView(CreateView):
    """Creates a new category."""

    model = Category
    form_class = CategoryForm
    template_name = "bdr/categories/category_add.html"

    # def form_valid(self, form):
    #     url = urlparse.urljoin(app_settings.STORAGE_URL, 'categories/')
    #     body = serialize(form.cleaned_data, exclude=['parent', 'href'])
    #     response, content = httplib2.Http().request(url, method='POST', body=json.dumps(body),
    #                                                 headers={'Content-Type': 'application/json'})
    #     if response.status != 201:
    #         details = json.loads(content)
    #         return self.render_to_response(self.get_context_data(form=form, remote_errors=details['errors']))
    #     return super(CategoryAddView, self).form_valid(form)