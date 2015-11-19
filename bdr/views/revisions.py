"""
This module defines classes for displaying and exporting revisions.
"""

from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import get_object_or_404, resolve_url
from django.utils.decorators import method_decorator
from django.views.decorators.gzip import gzip_page
from django.views.generic import DetailView, UpdateView, DeleteView, RedirectView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..models import Revision

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


def dispatch(request, view="export", *args, **kwargs):
    """
    Delegate response generation to a view able to handle the relevant format.

    :param request: The request HTTP received.
    :type request: django.http.HttpRequest
    :param view: The name of the view type being requested. One of: "export".
    :type view: str
    :param args: A list of view parameters extracted from the URL route.
    :type args: list of str
    :param kwargs: The keyword parameters extracted from the URL route.
    :type kwargs: dict of str
    :return: The response.
    :rtype: django.http.HttpResponse
    """
    if view == "export":
        target = get_object_or_404(Revision, pk=kwargs["rpk"]).format
    else:
        raise Http404
    try:
        view_func = target.views[view]
    except KeyError:
        return HttpResponseForbidden()
    return view_func(request, *args, **kwargs)


class LatestRevisionRedirectView(RedirectView):
    """
    This view determines the most recent revision of the file indicated in the
    request route and redirects the user to that instance.
    """

    permanent = False

    @classmethod
    def get_file(cls, *args, **kwargs):
        """
        Return the file as determined from the URL route arguments.

        :param args: The positional arguments extracted from the route.
        :param kwargs: The keyword arguments extracted from the route.
        :return: The identified file.
        :rtype: File
        :raise Http404: If the file does not exist.
        """
        from ..models import File
        return get_object_or_404(File, pk=kwargs["fpk"])

    @classmethod
    def get_latest_revision(cls, file):
        """
        Return the latest revision belonging to the given file.

        :param file: The file model instance to inspect.
        :type file: bdr.models.File
        :return: The latest revision.
        :rtype: Revision
        """
        revision = file.revisions.last()
        if revision is not None:
            return revision
        raise Http404("{:s} has no revisions.".format(file))

    def get_redirect_url(self, *args, **kwargs):
        """
        Return the URL to which this view shall redirect.

        :param args: The positional arguments extracted from the route.
        :param kwargs: The keyword arguments extracted from the route.
        :return: The destination URL.
        :rtype: str
        """
        path = kwargs.pop("path")
        file = self.get_file(*args, **kwargs)
        revision = self.get_latest_revision(file)
        kwargs.update(dict(rpk=revision.pk, revision=revision.number))
        return resolve_url("bdr:{:s}-revision".format(path), *args, **kwargs)


class RevisionDetailView(SearchableViewMixin, DetailView):
    """
    This view displays information about a given revision, including a link for
    downloading its content.

    This class overrides the get_context_data method of the `~DetailView`
    class.
    """

    model = Revision
    """Designate the model class used for obtaining data."""
    pk_url_kwarg = "rpk"
    template_name = "bdr/revisions/detail.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``file`` - this file model
         * ``tags`` - the tags annotating this revision

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(RevisionDetailView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.file.dataset
        context["file"] = self.object.file
        context["tags"] = self.object.tags.all()
        return context


class RevisionEditView(SearchableViewMixin, UpdateView):
    """This view is used to edit existing revisions."""

    model = Revision
    pk_url_kwarg = "rpk"
    template_name = "bdr/revisions/edit.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``dataset`` - the parent dataset model
         * ``file`` - this file model
         * ``revisions`` - the revisions of this file

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(RevisionEditView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.file.dataset
        context["file"] = self.object.file
        return context


class RevisionDeleteView(SearchableViewMixin, DeleteView):
    """This view is used to confirm deletion of an existing revision."""

    model = Revision
    pk_url_kwarg = "rpk"
    template_name = "bdr/revisions/confirm_delete.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the parent dataset model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(RevisionDeleteView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.file.dataset
        context["file"] = self.object.file
        return context

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        deleted.

        :return: The URL to redirect to once the object has been deleted.
        :rtype: str
        """
        return self.object.file.get_absolute_url()


class RevisionExportView(SearchableViewMixin, SingleObjectMixin, SessionWizardView):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.
    """

    context_object_name = "revision"
    model = Revision
    """Designate the model class used for obtaining data."""
    pk_url_kwarg = "rpk"
    templates = None

    def __init__(self, **kwargs):
        super(RevisionExportView, self).__init__(**kwargs)
        self.object = None  # type: Revision

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
        return super(RevisionExportView, self).get(request, *args, **kwargs)

    @method_decorator(gzip_page)
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
        return super(RevisionExportView, self).post(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        """
        Export this revision. Subclasses must override this method.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: The contents of this revision.
        :rtype: StreamingHttpResponse
        """
        raise NotImplementedError()

    def get_context_data(self, **kwargs):
        """
        Return the template context.

        This method returns a dictionary containing the variables for rendering
        this view. Available template context variables are:

         * ``dataset`` - the ancestral dataset model
         * ``file`` - the parent file model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(RevisionExportView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.file.dataset
        context["file"] = self.object.file
        return context

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

    # def render_to_streaming_response(self, records):
    #     response = StreamingHttpResponse(records, content_type="application/octet-stream")
    #     response["Content-Disposition"] = "attachment; filename={:s}".format(os.path.basename(self.object.file.name))
    #     return response
