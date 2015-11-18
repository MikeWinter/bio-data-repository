"""
This module defines classes for displaying and editing sources.
"""

from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin

from . import SearchableViewMixin
from ..forms import SourceForm
from ..models import Dataset, Source

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


class SourceListView(SearchableViewMixin, SingleObjectMixin, ListView):
    """Lists sources associated with a dataset."""

    model = Dataset
    paginate_by = 10
    paginate_orphans = 2
    pk_url_kwarg = "dpk"
    template_name = "bdr/sources/source_list.html"

    def __init__(self, **kwargs):
        super(SourceListView, self).__init__(**kwargs)
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
        return super(SourceListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of sources associated with this dataset.

        :return: The files associated with this dataset.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return self.object.sources.all()


class SourceDetailView(SearchableViewMixin, SingleObjectMixin, ListView):
    """
    This view displays the details of a data source, including a list of its
    filters.

    This class overrides the get and get_queryset methods of the `~ListView`
    and `~SingleObjectMixin` classes, respectively.
    """

    keys = ["up", "down"]
    model = Source
    paginate_by = 10
    paginate_orphans = 2
    pk_url_kwarg = "source"
    template_name = "bdr/sources/source_detail.html"

    def __init__(self, **kwargs):
        super(SourceDetailView, self).__init__(**kwargs)
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
        return super(SourceDetailView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Send a response for HTTP POST requests sent to this view.

        :param request: The request received by the view.
        :type request: django.http.HttpRequest
        :param args: The positional arguments captured from the route for this
                     view.
        :param kwargs: The named arguments captured from the route for this
                       view.
        :return: The response.
        :rtype: django.http.HttpResponseBase
        """
        instance = self.get_object(queryset=self.model.objects.all())
        direction = self._get_direction()
        filter_pk = long(request.POST.get(direction))
        order = instance.get_filter_order()
        index = order.index(filter_pk)
        if direction == "up" and index > 0:
            order[index - 1:index + 1] = reversed(order[index - 1:index + 1])
        elif direction == "down" and index < (len(order) - 1):
            order[index:index + 2] = reversed(order[index:index + 2])
        instance.set_filter_order(order)
        return redirect(instance)

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``source`` - this source model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(SourceDetailView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.dataset
        context["filters"] = context["object_list"]
        return context

    def get_queryset(self):
        """
        Get the list of filters associated with this data source.

        :return: The filters associated with this source.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return [self.object.filters.get(pk=pk) for pk in self.object.get_filter_order()]

    def _get_direction(self):
        directions = [key for key in self.request.POST if key in self.keys]
        if len(directions) == 1:
            return directions[0]
        raise SuspiciousOperation("Invalid/missing direction")


class SourceAddView(SearchableViewMixin, CreateView):
    """Used to create a new source."""

    model = Source
    form_class = SourceForm
    pk_url_kwarg = "dpk"
    template_name = "bdr/sources/source_add.html"

    def __init__(self, **kwargs):
        super(SourceAddView, self).__init__(**kwargs)
        self.dataset = None
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch request to an appropriate HTTP method handler and return the
        response.

        :param request: The HTTP request.
        :param args: Positional arguments derived from the route to this view.
        :param kwargs: Keyword arguments derived from the route to this view.
        :return: The HTTP response.
        """
        self.dataset = get_object_or_404(Dataset, pk=kwargs["dpk"])
        return super(SourceAddView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``form`` - the form for collecting source data

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(SourceAddView, self).get_context_data(**kwargs)
        context["dataset"] = self.dataset
        return context

    def form_valid(self, form):
        """
        Save the model associated with the validated form.

        :param form: A form containing validated data for creating the object.
        :type form: django.forms.ModelForm
        :return: The response to this request.
        :rtype: django.http.HttpResponse
        """
        self.object = form.save(False)
        self.object.dataset = self.dataset
        self.object.save()
        form.save_m2m()
        return super(ModelFormMixin, self).form_valid(form)


class SourceEditView(SearchableViewMixin, UpdateView):
    """User to edit an existing source."""

    model = Source
    form_class = SourceForm
    pk_url_kwarg = "source"
    template_name = "bdr/sources/source_edit.html"

    def get_queryset(self):
        """
        Return the queryset to look an object up against.

        :return: The queryset.
        :rtype: django.db.models.query.QuerySet
        """
        dataset = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        queryset = super(SourceEditView, self).get_queryset()
        return queryset.filter(dataset__exact=dataset)

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``form`` - the form for collecting source data

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(SourceEditView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.dataset
        return context


class SourceDeleteView(SearchableViewMixin, DeleteView):
    """This view is used to confirm deletion of an existing source."""

    model = Source
    pk_url_kwarg = "source"
    template_name = "bdr/sources/source_confirm_delete.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``form`` - the form for collecting source data

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(SourceDeleteView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.dataset
        return context

    def get_queryset(self):
        """
        Return the queryset to look an object up against.

        :return: The queryset.
        :rtype: django.db.models.query.QuerySet
        """
        dataset = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        queryset = super(SourceDeleteView, self).get_queryset()
        return queryset.filter(dataset__exact=dataset)

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        deleted.

        :return: The URL to redirect to once the object has been deleted.
        :rtype: str
        """
        return self.object.dataset.get_absolute_url()
