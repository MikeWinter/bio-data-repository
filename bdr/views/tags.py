"""
This module defines classes for displaying and editing tags.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.views.generic import ListView, UpdateView, CreateView, DeleteView, DetailView

from . import SearchableViewMixin
from ..forms import TagForm
from ..models import Tag

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


class TagListView(SearchableViewMixin, ListView):
    """
    This view displays the list of tags used to annotate objects in the
    repository.

    The list can be controlled using the following GET query parameters:

        query
            A space-separated list of complete or partial words in the name of
            the tags to be retrieved. If more than one word is specified, all
            must be present for a tag to be matched though not necessary in
            the order given. If the hash (#) is used to prefix a word, it will
            only match the first word in a tag name.
        sort_by
            The name of a field by which the list is sorted. If the given field
            is not available, the default sorting order will be used.
        order
            The direction of the ordering: ``asc`` (ascending) or ``desc``
            (descending).
        limit
            The maximum number of tags to return at a time. If there are more
            results than the limit, these can be retrieved using the ``page``
            parameter.
        page
            A number indicating which page to display, or the word ``last`` to
            select the final page.
    """

    context_object_name = 'tags'
    model = Tag
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/tags/tag_list.html"

    def get_queryset(self):
        """
        Get the list of tags for this view.

        The list may be filtered and sorted using the request parameters
        "query" and "sort_by", respectively. The result order can be determined
        using the "order" request parameter. See the class description for more
        information.

        :return: The tags for this view.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        queryset = super(TagListView, self).get_queryset()

        if self.request.method == "GET" and "query" in self.request.GET:
            for token in self.request.GET["query"].split():
                if token.startswith("#"):
                    kwargs = dict(name__istartswith=token[1:])
                else:
                    kwargs = dict(name__icontains=token)
                queryset = queryset.filter(**kwargs)

            if "sort_by" in self.request.GET:
                field = self.request.GET["sort_by"]
                if field in self.model.get_field_names():
                    queryset = queryset.order_by(field)

            if self.request.GET.get("order") == "desc":
                queryset = queryset.reverse()

        return queryset

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by, or ``None`` for no pagination.

        This limit may be obtained from the "limit" request parameter,
        otherwise it will fallback to the value given by the `paginate_by`
        property.

        :param queryset: The items to be displayed by this view.
        :type queryset: ``django.db.models.query.QuerySet`` | list
        :return: The number of items to display, or ``None`` for all.
        :rtype: int | None
        """
        default = super(TagListView, self).get_paginate_by(queryset)
        try:
            limit = int(self.request.GET.get("limit", default))
        except ValueError:
            limit = default
        return limit

    def render_to_response(self, context, **response_kwargs):
        """
        Returns a response with a template rendered using the given context.

        If any keyword arguments are provided, they will be passed to the
        constructor of the response class.

        If the response is generated for an Ajax request, it is rendered into a
        JSON-formatted string.

        :param context: A dictionary of template variables.
        :type context: dict of str
        :param response_kwargs: Arguments for initialising the response class.
        :type response_kwargs: dict of str
        :return: The response.
        :rtype: HttpResponse | django.template.response.TemplateResponse
        """
        if self.request.is_ajax():
            return self.render_to_json_response(context, **response_kwargs)

        return super(TagListView, self).render_to_response(context, **response_kwargs)

    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON-formatted response using the given context.

        If any keyword arguments are provided, they will be passed to the
        constructor of the response class.

        :param context: A dictionary of context variables.
        :type context: dict of str
        :param response_kwargs: Arguments for initialising the response class.
        :type response_kwargs: dict of str
        :return: The response.
        :rtype: HttpResponse
        """
        tags = context["page_obj"] if context["is_paginated"] else self.object_list
        content = json.dumps([
            {"name": tag.name, "href": tag.get_absolute_url()} for tag in tags
        ], cls=DjangoJSONEncoder)
        return HttpResponse(content, content_type="application/json", **response_kwargs)


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
    success_url = reverse_lazy("bdr:tags")
    template_name = "bdr/tags/tag_confirm_delete.html"
