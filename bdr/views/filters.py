"""
This module defines classes for displaying and editing filters.
"""

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.edit import ModelFormMixin

from . import SearchableViewMixin
from ..forms import FilterForm
from ..models import Dataset, Filter, Source

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


class FilterTestMixin(object):
    """
    This mixin extracts the testing of filter pattern against sample file names
    common to both the :py:class:`FilterAddView` and :py:class:`FilterEditView`
    classes.
    """

    feedback_classes = "has-feedback {type:s}"
    failure_class = "has-error"
    failure_message = "does not match"
    success_class = "has-success"
    success_message = "matches"

    def get_test_response(self, data, form):
        """
        Produce a template response showing the result of the pattern test.

        :param data: The data submitted by the user containing the sample value.
        :type data: dict of (str | unicode)
        :param form: The form that describes the filter under construction.
        :type form: FilterForm
        :return: The response to return to the client.
        :rtype: django.template.response.TemplateResponse
        """
        if data.get("op") == "test":
            filename = data.get("filename", "")
            matches = form.instance.match(filename)
            mapped_to = form.instance.map(filename) if matches else None
            class_names = self.feedback_classes.format(
                type=self.success_class if matches else self.failure_class)
            message = self.success_message if matches else self.failure_message
            return self.render_to_response(self.get_context_data(form=form,
                                                                 class_names=class_names,
                                                                 filename=filename,
                                                                 matches=matches,
                                                                 mapped_to=mapped_to,
                                                                 message=message))
        return None


class FilterAddView(FilterTestMixin, SearchableViewMixin, CreateView):
    """Used to create a new filter."""

    model = Filter
    form_class = FilterForm
    pk_url_kwarg = "filter"
    template_name = "bdr/filters/add.html"

    def __init__(self, **kwargs):
        super(FilterAddView, self).__init__(**kwargs)
        self.dataset = None
        self.object = None
        self.source = None

    def dispatch(self, request, *args, **kwargs):
        """
        Respond to a request by invoking the request handler relevant to the
        HTTP method.

        :param request: The HTTP request.
        :type request: django.http.HttpRequest
        :param args: A list of view parameters extracted from the URL route.
        :type args: list of str
        :param kwargs: The keyword parameters extracted from the URL route.
        :type kwargs: dict of str
        :return: The response.
        :rtype: django.http.HttpResponse
        """
        self.dataset = get_object_or_404(Dataset, pk=kwargs["dpk"])
        self.source = get_object_or_404(Source, pk=kwargs["source"])
        return super(FilterAddView, self).dispatch(request, *args, **kwargs)

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
        context = super(FilterAddView, self).get_context_data(**kwargs)
        context["dataset"] = self.dataset
        context["source"] = self.source
        return context

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        added.

        :return: The URL to redirect to once the object has been added.
        :rtype: str
        """
        return reverse("bdr:view-source", kwargs=dict(source=self.source.pk, dpk=self.dataset.pk,
                                                      dataset=slugify(unicode(self.dataset.name))))

    def form_valid(self, form):
        """
        Save the model associated with the validated form.

        If the form was submitted in response to the <em>Test</em> button, the
        form is re-rendered with the result of the test.

        :param form: A form containing validated data for creating the object.
        :type form: FilterForm
        :return: The response to this request.
        :rtype: django.http.HttpResponse
        """
        response = self.get_test_response(self.request.POST, form)
        if response:
            return response

        self.object = form.save(False)
        self.object.source = self.source
        self.object.save()
        form.save_m2m()
        return super(ModelFormMixin, self).form_valid(form)


class FilterEditView(FilterTestMixin, SearchableViewMixin, UpdateView):
    """User to edit an existing filter."""

    model = Filter
    form_class = FilterForm
    pk_url_kwarg = "filter"
    template_name = "bdr/filters/edit.html"

    def __init__(self, **kwargs):
        super(FilterEditView, self).__init__(**kwargs)
        self.dataset = None
        self.source = None

    def form_valid(self, form):
        """
        Save the model associated with the validated form.

        If the form was submitted in response to the <em>Test</em> button, the
        form is re-rendered with the result of the test.

        :param form: A form containing validated data for creating the object.
        :type form: FilterForm
        :return: The response to this request.
        :rtype: django.http.HttpResponse
        """
        response = self.get_test_response(self.request.POST, form)
        if response:
            return response
        return super(FilterEditView, self).form_valid(form)

    def get_queryset(self):
        """
        Return the queryset to look an object up against.

        :return: The queryset.
        :rtype: django.db.models.query.QuerySet
        """
        self.dataset = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        self.source = get_object_or_404(Source, pk=self.kwargs["source"])
        queryset = super(FilterEditView, self).get_queryset()
        return queryset.filter(source__exact=self.source)

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the ancestral dataset model
         * ``form`` - the form for collecting source data
         * ``source`` - the model for the parent source model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(FilterEditView, self).get_context_data(**kwargs)
        context["source"] = self.source
        context["dataset"] = self.dataset
        return context

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        updated.

        :return: The URL to redirect to once the object has been updated.
        :rtype: str
        """
        return self.source.get_absolute_url()


class FilterDeleteView(SearchableViewMixin, DeleteView):
    """This view is used to confirm deletion of an existing filter."""

    model = Filter
    pk_url_kwarg = "filter"
    template_name = "bdr/filters/confirm_delete.html"

    def __init__(self, **kwargs):
        super(FilterDeleteView, self).__init__(**kwargs)
        self.dataset = None
        self.source = None

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
        context = super(FilterDeleteView, self).get_context_data(**kwargs)
        context["dataset"] = self.dataset
        context["source"] = self.source
        return context

    def get_queryset(self):
        """
        Return the queryset to look an object up against.

        :return: The queryset.
        :rtype: django.db.models.query.QuerySet
        """
        self.dataset = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        self.source = get_object_or_404(Source, pk=self.kwargs["source"])
        queryset = super(FilterDeleteView, self).get_queryset()
        return queryset.filter(source__exact=self.source)

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        deleted.

        :return: The URL to redirect to once the object has been deleted.
        :rtype: str
        """
        return self.source.get_absolute_url()
