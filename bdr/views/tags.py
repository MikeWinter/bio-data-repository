"""
This module defines classes for displaying and editing tags.
"""

from django.core.urlresolvers import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView

from . import SearchableViewMixin
from ..forms import TagForm
from ..models import Tag

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


class TagListView(SearchableViewMixin, ListView):
    """
    This view displays the list of tags used to annotate objects in the
    repository.
    """

    context_object_name = 'tags'
    model = Tag
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/tags/tag_list.html"

    # def get_queryset(self):
    #     queryset = self.model.objects.fetch_all()
    #
    #     if self.request.method == 'GET' and 'filter' in self.request.GET:
    #         query = self.request.GET['filter']
    #         matched = False
    #         for token in query.split():
    #             if token.startswith('#'):
    #                 matched = True
    #                 queryset = queryset.filter(name__istartswith=token[1:])
    #         if not matched:
    #             queryset = queryset.none()
    #     return queryset

    # def render_to_response(self, context, **response_kwargs):
    #     if not self.request.is_ajax():
    #         return super(TagListView, self).render_to_response(context, **response_kwargs)
    #
    #     results = [{'name': '#%s' % obj.name, 'href': None} for obj in context['tags']]
    #     return HttpResponse(json.dumps(results), content_type='application/json',
    #                         **response_kwargs)


class TagAddView(SearchableViewMixin, CreateView):
    """Used to create a new dataset."""

    model = Tag
    form_class = TagForm
    template_name = "bdr/tags/tag_add.html"


class TagDetailView(SearchableViewMixin, DetailView):
    """
    This view displays the datasets, files and revisions associated with a
    given tag.
    """

    model = Tag
    paginate_by = 10
    paginate_orphans = 2
    supported_objects = ("datasets", "files", "revisions")
    template_name = "bdr/tags/tag_detail.html"


class TagEditView(SearchableViewMixin, UpdateView):
    """Edits existing tags."""

    form_class = TagForm
    model = Tag
    template_name = "bdr/tags/tag_edit.html"


class TagDeleteView(SearchableViewMixin, DeleteView):
    """Deletes an existing category."""

    model = Tag
    success_url = reverse_lazy("bdr.frontend:tags")
    template_name = "bdr/tags/tag_confirm_delete.html"
