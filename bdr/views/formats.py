"""
This module defines classes for displaying and editing formats.
"""

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from . import SearchableViewMixin
from ..formats import get_entry_point as get_format_entry_point, get_realisable_formats
from ..models import Format

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


def dispatch(request, view="view", *args, **kwargs):
    """
    Delegate response generation to a view able to handle the relevant format.

    :param request: The request HTTP received.
    :type request: django.http.HttpRequest
    :param view: The name of the view type being requested. One of: "create",
                 "edit", "delete", "view" or "export".
    :type view: str
    :param args: A list of view parameters extracted from the URL route.
    :type args: list of str
    :param kwargs: The keyword parameters extracted from the URL route.
    :type kwargs: dict of str
    :return: The response.
    :rtype: django.http.HttpResponse
    """
    if view == "create":
        target = get_format_entry_point(kwargs["slug"])
        kwargs["name"] = target.name
    else:
        target = get_object_or_404(Format, *args, **kwargs)
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
    template_name = "bdr/formats/format_list.html"

    def get_context_data(self, **kwargs):
        context = super(FormatListView, self).get_context_data(**kwargs)
        context["realisable_formats"] = [{"name": obj.name, "entry_point_name": obj.entry_point_name}
                                         for obj in get_realisable_formats()]
        return context


class FormatDetailView(SearchableViewMixin, DetailView):
    """
    This view displays the details of a format, including a list of its fields.
    """

    model = Format
    template_name = "bdr/formats/format_detail.html"


class FormatCreateView(CreateView):
    """
    Used to create a new format.


    """
    model = Format
    template_name = "bdr/formats/format_create.html"

    def __init__(self, **kwargs):
        super(FormatCreateView, self).__init__(**kwargs)
        self.object = None

    def get_context_data(self, **kwargs):
        context = super(FormatCreateView, self).get_context_data(**kwargs)
        context["id"] = self.kwargs["slug"]
        context["name"] = self.kwargs["name"]
        context["realisable_formats"] = [{"name": obj.name, "entry_point_name": obj.entry_point_name}
                                         for obj in get_realisable_formats()]
        return context


class FormatEditView(UpdateView):
    """This view is used to edit existing formats."""

    model = Format
    template_name = "bdr/formats/format_edit.html"

    def __init__(self, **kwargs):
        super(FormatEditView, self).__init__(**kwargs)
        self.object = None


class FormatDeleteView(DeleteView):
    """
    This view is used to confirm the deletion of an existing format.

    Files and revisions using the deleted format are subsequently marked as
    containing raw data.
    """

    model = Format
    success_url = reverse_lazy("bdr:formats")
    template_name = "bdr/formats/format_confirm_delete.html"
