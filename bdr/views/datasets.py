"""
This module defines classes for displaying and editing datasets.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..forms import DatasetForm
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

    This class overrides the get and get_queryset methods of the `~ListView`
    and `~SingleObjectMixin` classes, respectively.
    """

    model = Dataset
    paginate_by = 10
    paginate_orphans = 2
    pk_url_kwarg = "dpk"
    template_name = "bdr/datasets/dataset_detail.html"

    def __init__(self, **kwargs):
        super(DatasetDetailView, self).__init__(**kwargs)
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
        return super(DatasetDetailView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of files associated with this dataset.

        :return: The files associated with this dataset.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return self.object.files.all()


class DatasetListView(SearchableViewMixin, ListView):
    """
    This view displays a list of datasets stored in the repository.

    The list can be controlled using the following GET query parameters:

        query
            A space-separated list of complete or partial words in the name of
            the datasets to be retrieved. If more than one word is specified,
            all must be present for a dataset to be matched though not
            necessary in the order given.
        sort_by
            The name of a field by which the list is sorted. If the given field
            is not available, the default sorting order will be used.
        order
            The direction of the ordering: ``asc`` (ascending) or ``desc``
            (descending).
        limit
            The maximum number of datasets to return at a time. If there are
            more results than the limit, these can be retrieved using the
            ``page`` parameter.
        page
            A number indicating which page to display, or the word ``last`` to
            select the final page.
    """

    context_object_name = "datasets"
    model = Dataset
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/datasets/dataset_list.html"

    def get_queryset(self):
        """
        Get the list of datasets for this view.

        The list may be filtered and sorted using the request parameters
        "query" and "sort_by", respectively. The result order can be determined
        using the "order" request parameter. See the class description for more
        information.

        :return: The datasets for this view.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        queryset = super(DatasetListView, self).get_queryset()

        if self.request.method == "GET" and "query" in self.request.GET:
            for token in self.request.GET["query"].split():
                queryset = queryset.filter(name__icontains=token)

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
        default = super(DatasetListView, self).get_paginate_by(queryset)
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

        return super(DatasetListView, self).render_to_response(context, **response_kwargs)

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
        datasets = context["page_obj"] if context["is_paginated"] else self.object_list
        content = json.dumps([
            {"name": dataset.name, "href": dataset.get_absolute_url()} for dataset in datasets
        ], cls=DjangoJSONEncoder)
        return HttpResponse(content, content_type="application/json", **response_kwargs)


class DatasetEditView(SearchableViewMixin, UpdateView):
    """This view is used to edit existing datasets."""

    model = Dataset
    form_class = DatasetForm
    pk_url_kwarg = "dpk"
    template_name = "bdr/datasets/dataset_edit.html"


class DatasetAddView(SearchableViewMixin, CreateView):
    """Used to create a new dataset."""

    model = Dataset
    form_class = DatasetForm
    template_name = "bdr/datasets/dataset_add.html"


class DatasetDeleteView(SearchableViewMixin, DeleteView):
    """This view is used to confirm deletion of an existing dataset."""

    model = Dataset
    pk_url_kwarg = "dpk"
    success_url = reverse_lazy('bdr:datasets')
    template_name = "bdr/datasets/dataset_confirm_delete.html"
