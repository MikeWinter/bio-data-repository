"""
This module defines classes for displaying and editing formats.
"""

from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..formats import get_entry_point as get_format_entry_point, get_realisable_formats
from ..models import Format

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


def dispatch(request, view="view", *args, **kwargs):
    """
    Delegate response generation to a view able to handle the relevant format.

    :param request: The request HTTP received.
    :type request: django.http.HttpRequest
    :param view: The name of the view type being requested. One of: "create",
                 "edit", "delete" or "view".
    :type view: str
    :param args: A list of view parameters extracted from the URL route.
    :type args: list of str
    :param kwargs: The keyword parameters extracted from the URL route.
    :type kwargs: dict of str
    :return: The response.
    :rtype: django.http.HttpResponse
    """
    if view == "create":
        target = get_format_entry_point(kwargs["type"])
        kwargs["name"] = target.name
    else:
        target = get_object_or_404(Format, pk=kwargs["pk"])
    try:
        view_func = target.views[view]
    except KeyError:
        return HttpResponseForbidden()
    return view_func(request, *args, **kwargs)


class FormatListView(SearchableViewMixin, ListView):
    """
    This view displays a list of formats describing files in the repository.
    """

    context_object_name = "formats"
    model = Format
    paginate_by = 10
    paginate_orphans = 2
    template_name = "bdr/formats/list.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``realisable_formats`` - a dictionary of the names and entry points
                                    of formats that can be customised

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(FormatListView, self).get_context_data(**kwargs)
        context["realisable_formats"] = [{"name": obj.name, "entry_point_name": obj.entry_point_name}
                                         for obj in get_realisable_formats()]
        return context


class FormatDetailView(SearchableViewMixin, DetailView):
    """
    This view displays the details of a format, including a list of its fields.
    """

    context_object_name = "format"
    model = Format


class FormatCreateView(SessionWizardView):
    """
    Used to create a new format.
    """

    model = Format
    templates = None

    def done(self, form_list, **kwargs):
        """
        Add the definition of this format to the repository. Subclasses must
        override this method.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: A redirect response to a view of this new format.
        :rtype: HttpResponseRedirect
        """
        raise NotImplementedError()

    def get_context_data(self, form, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``type`` - the entry point identifier for this type of format
         * ``name`` - the display name for this type of format
         * ``realisable_formats`` - a dictionary of the names and entry points
                                    of formats that can be customised

        :param form: The form or formset instance displayed in this step.
        :type form: Form | BaseFormSet
        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(FormatCreateView, self).get_context_data(form, **kwargs)
        context["type"] = self.kwargs["type"]
        context["name"] = self.kwargs["name"]
        context["realisable_formats"] = [{"name": obj.name, "entry_point_name": obj.entry_point_name}
                                         for obj in get_realisable_formats()]
        return context

    def get_template_names(self):
        """
        Return a list of template names to be used for the current step in this
        view.

        :return: A list of template names for the current step in this view.
        :rtype: list of str
        """
        if self.templates is None:
            raise ImproperlyConfigured("FormatCreateView requires either a dictionary of templates defined in the"
                                       " templates class attribute or for get_template_names() to be overridden.")
        return [self.templates[self.steps.current]]


class FormatEditView(SingleObjectMixin, SessionWizardView):
    """This view is used to edit existing formats."""

    context_object_name = "format"
    model = Format
    templates = None

    def __init__(self, **kwargs):
        super(FormatEditView, self).__init__(**kwargs)
        self.object = None

    def done(self, form_list, **kwargs):
        """
        Modify the definition of this format. Subclasses must override this
        method.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: A redirect response to a view of this format.
        :rtype: HttpResponseRedirect
        """
        raise NotImplementedError()

    def get(self, request, *args, **kwargs):
        """
        Respond to a GET request.

        :param request: The HTTP request.
        :type request: django.http.HttpRequest
        :param args: A list of view parameters extracted from the URL route.
        :type args: list of str
        :param kwargs: The keyword parameters extracted from the URL route.
        :type kwargs: dict of str
        :return: The response.
        :rtype: django.http.HttpResponse
        """
        self.object = self.get_object()
        return super(FormatEditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Respond to a POST request.

        :param request: The HTTP request.
        :type request: django.http.HttpRequest
        :param args: A list of view parameters extracted from the URL route.
        :type args: list of str
        :param kwargs: The keyword parameters extracted from the URL route.
        :type kwargs: dict of str
        :return: The response.
        :rtype: django.http.HttpResponse
        """
        self.object = self.get_object()
        return super(FormatEditView, self).post(request, *args, **kwargs)

    def get_template_names(self):
        """
        Return a list of template names to be used for the current step in this
        view.

        :return: A list of template names for the current step in this view.
        :rtype: list of str
        """
        if self.templates is None:
            raise ImproperlyConfigured("FormatEditView requires either a dictionary of templates defined in the"
                                       " templates class attribute or for get_template_names() to be overridden.")
        return [self.templates[self.steps.current]]


class FormatDeleteView(DeleteView):
    """
    This view is used to confirm the deletion of an existing format.

    Files and revisions using the deleted format are subsequently marked as
    containing raw data.
    """

    model = Format
    success_url = reverse_lazy("bdr:formats")
