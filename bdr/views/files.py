"""
This module defines classes for displaying and editing files.
"""

import os.path

from django.conf import settings
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.views.generic import ListView, UpdateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from . import SearchableViewMixin
from ..forms import UploadForm, FileForm, FileContentSelectionForm
from ..forms.sets import FileContentSelectionFormSet
from ..models import Dataset, File
from ..utils import RemoteFile
from ..utils.archives import Archive

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


class FileListView(SearchableViewMixin, SingleObjectMixin, ListView):
    """Lists files associated with a dataset."""

    model = Dataset
    paginate_by = 10
    paginate_orphans = 2
    pk_url_kwarg = "dpk"
    template_name = "bdr/files/file_list.html"

    def __init__(self, **kwargs):
        super(FileListView, self).__init__(**kwargs)
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
        return super(FileListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get the list of files associated with this dataset.

        :return: The files associated with this dataset.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return self.object.files.all()


class FileDetailView(SearchableViewMixin, SingleObjectMixin, ListView):
    """
    This view displays information about a given file, including a list of its
    revisions and links for downloading their content.

    This class overrides the get and get_queryset methods of the `~ListView`
    and `~SingleObjectMixin` classes, respectively.
    """

    model = File
    """Designate the model class used for obtaining data."""
    paginate_by = 10
    paginate_orphans = 2
    pk_url_kwarg = "fpk"
    template_name = "bdr/files/file_detail.html"

    def __init__(self, **kwargs):
        super(FileDetailView, self).__init__(**kwargs)
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
        return super(FileDetailView, self).get(request, *args, **kwargs)

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
        context = super(FileDetailView, self).get_context_data(**kwargs)
        context["dataset"] = self.object.dataset
        return context

    def get_queryset(self):
        """
        Get the list of revisions associated with this file.

        :return: The revisions associated with this file.
        :rtype: ``django.db.models.query.QuerySet`` | list
        """
        return self.object.revisions.all()


class FileUploadView(SearchableViewMixin, SessionWizardView):
    """
    This view guides the user through uploading a file and adding its contents
    to the repository.

    This class overrides the `done`, `get_context_data` and `get_form_initial`
    methods of the `~SessionWizardView` class, and the `get_template_names`
    method of the `~TemplateView` class.
    """

    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "tmp"))
    form_list = [
        ("upload", UploadForm),
        ("selection", formset_factory(FileContentSelectionForm, formset=FileContentSelectionFormSet,
                                      extra=0)),
    ]
    templates = {
        "upload": "bdr/files/file_upload.html",
        "selection": "bdr/files/file_content_selection.html",
    }

    def __init__(self, **kwargs):
        super(FileUploadView, self).__init__(**kwargs)
        self.dataset = None

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
        return super(FileUploadView, self).dispatch(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        """
        Add the contents of the uploaded file to the repository and redirect
        back to the parent dataset.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: A redirect response to a view of the parent dataset.
        :rtype: HttpResponseRedirect
        """
        with self.get_uploaded_archive() as archive:
            filename = archive.file.name
            update = self.dataset.updates.create(size=self.file_storage.size(filename),
                                                 source=None)

            for file_mapping in self.get_cleaned_data_for_step("selection"):
                if file_mapping["mapped_name"] is None:
                    continue

                member = archive[file_mapping["real_name"]]  # :type: Member
                data = RemoteFile(member.file, file_mapping["mapped_name"], member.size,
                                  member.mtime)
                default_format = file_mapping["format"]  # :type: Format
                self.dataset.add_file(data, update, default_format)

        try:
            # TODO: Create management command to periodically clean out the
            # TODO: temporary storage in case deletion fails.
            self.file_storage.delete(filename)
        except OSError as err:
            import errno
            if err.errno != errno.EACCES:  # Ignore deletion failure on Windows
                raise

        uri = reverse("bdr:view-dataset",
                      kwargs=dict(dpk=self.dataset.pk, dataset=slugify(unicode(self.dataset.name))))
        return HttpResponseRedirect(uri)

    def get_context_data(self, form, **kwargs):
        """
        Return the template context for a step.

        This method returns a dictionary containing variables for the rendered
        form step. Available template context variables are:

         * all extra data stored in the storage backend
         * ``wizard`` - a dictionary representation of the wizard instance
         * ``dataset`` - the parent dataset model

        :param form: The form to display in this step.
        :type form: django.forms.Form
        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(FileUploadView, self).get_context_data(form=form, **kwargs)
        context["dataset"] = self.dataset
        return context

    def get_form_initial(self, step):
        """
        Returns a dictionary, or list of dictionaries, which will be passed to
        the form for `step` as `initial`.

        :param step: The name of the current step.
        :type step: str
        :return: A dictionary, or list of dictionaries, that provides initial
                 data for the forms in this view.
        :rtype: dict | list of dict
        """
        if step == "selection":
            archive = self.get_uploaded_archive()
            return [{"real_name": member, "mapped_name": member} for member in archive]
        return super(FileUploadView, self).get_form_initial(step)

    def get_template_names(self):
        """
        Return a list of template names to be used for the current step in this
        view.

        :return: A list of template names for the current step in this view.
        :rtype: list of str
        """
        return [self.templates[self.steps.current]]

    def get_uploaded_archive(self):
        """
        Return the archive uploaded in the first step of this view.

        :return: The uploaded archive.
        :rtype: Archive
        """
        archive = None
        data = self.get_cleaned_data_for_step("upload") or {}
        uploaded_file = data.get("file")
        if uploaded_file:
            path = self.file_storage.path(uploaded_file.name)
            archive = Archive.instance(uploaded_file, path)
        return archive


class FileEditView(SearchableViewMixin, UpdateView):
    """This view is used to edit existing files."""

    model = File
    form_class = FileForm
    pk_url_kwarg = "fpk"
    template_name = "bdr/files/file_edit.html"

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
        context = super(FileEditView, self).get_context_data(**kwargs)
        context["dataset"] = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        return context


class FileDeleteView(SearchableViewMixin, DeleteView):
    """This view is used to confirm deletion of an existing file."""

    model = File
    pk_url_kwarg = "fpk"
    template_name = "bdr/files/file_confirm_delete.html"

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
        context = super(FileDeleteView, self).get_context_data(**kwargs)
        context["dataset"] = get_object_or_404(Dataset, pk=self.kwargs["dpk"])
        return context

    def get_success_url(self):
        """
        Return the URL to redirect to when the object has been successfully
        deleted.

        :return: The URL to redirect to once the object has been deleted.
        :rtype: str
        """
        return self.object.dataset.get_absolute_url()
