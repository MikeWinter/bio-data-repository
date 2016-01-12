import os.path

from django.http import StreamingHttpResponse

from .forms import DrugBank43ExportForm
from ...models import Revision
from ...views.revisions import RevisionExportView


class DrugBank43RevisionExportView(RevisionExportView):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.
    """

    form_list = [
        # ("options", SimpleFormatExportOptionsForm),
        ("fields", DrugBank43ExportForm),
    ]
    model = Revision
    templates = {
        # "options": "bdr/revisions/simple/export_options.html",
        "fields": "bdr/revisions/drugbank43/export_fields.html",
    }

    def done(self, form_list, **kwargs):
        """
        Export this revision.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: The contents of this revision.
        :rtype: StreamingHttpResponse
        """
        options_form, fields_form \
            = form_list  # type: SimpleFormatExportOptionsForm, SimpleFormatFieldSelectionFormSet
        field_names = fields_form.cleaned_metadata['selected']
        options = options_form.cleaned_metadata

        iterator = self.object.format.convert(self.object.data, field_names, **options)
        response = StreamingHttpResponse(iterator, content_type="application/octet-stream")
        response["Content-Disposition"] = "attachment; filename={:s}".format(os.path.basename(self.object.file.name))
        return response

    def get_form_initial(self, step):
        """
        Return a dictionary which will define the initial data for the form for
        ``step``. If no initial data was provided while initializing the form
        wizard, a empty dictionary will be returned.

        :param step: The name of the current step.
        :type step: str
        :return: The initial form data.
        :rtype: dict of unicode
        """
        # if step == "fields":
        #     return self.object.format.fields
        return super(DrugBank43RevisionExportView, self).get_form_initial(step)

    def get_form_instance(self, step):
        """
        Return a model instance which will be passed to the form for ``step``.
        If no instance object was provided while initializing the form wizard,
        None will be returned.

        :param step: The name of the current step.
        :type step: str
        :return: The model object.
        :rtype: Model
        """
        if step == "options":
            return self.object.format
        return super(DrugBank43RevisionExportView, self).get_form_instance(step)
