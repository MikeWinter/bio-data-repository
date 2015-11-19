"""
This module defines classes for displaying and editing simple type formats.
"""

try:
    # noinspection PyPep8Naming
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import unicodedata

from django.forms.formsets import formset_factory
from django.http import StreamingHttpResponse
from django.shortcuts import redirect

from ...models.simple import SimpleFormat, SimpleRevision
from ...views.formats import FormatDetailView, FormatCreateView, FormatEditView, FormatDeleteView
from ...views.revisions import RevisionExportView
from .forms import (SimpleFormatForm, SimpleFormatExportOptionsForm, SimpleFormatFieldForm, SimpleFormatFieldFormSet,
                    SimpleFormatFieldSelectionForm, SimpleFormatFieldSelectionFormSet)

__all__ = ["Record", "Reader", "Writer"]
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


class SimpleFormatDetailView(FormatDetailView):
    """
    This view displays the details of a format, including a list of its fields.
    """

    CONTROL_NAMES = {
        u"\a": "Bell (BEL)",
        u"\b": "Backspace (BS)",
        u"\f": "Form feed (FF)",
        u"\n": "Line feed (LF)",
        u"\r": "Carriage return (CR)",
        u"\t": "Horizontal tab (TAB)",
        u"\v": "Vertical tab (VT)",
    }

    model = SimpleFormat
    template_name = "bdr/formats/simple/detail.html"

    def get_context_data(self, **kwargs):
        """
        Return the template context for this view.

        This method returns a dictionary containing variables for the rendered
        view. Available template context variables are:

         * ``fields`` - a list of fields used by this instance
         * ``format`` - the format model

        :param kwargs: A mapping of extra data available for use in templates.
        :type kwargs: dict of str
        :return: A dictionary of template variables and values.
        :rtype: dict of str
        """
        context = super(SimpleFormatDetailView, self).get_context_data(**kwargs)
        for attr in ["comment", "escape", "quote", "separator"]:
            character = getattr(self.object, attr, "")
            if character != "" and self.is_symbol(character):
                context[attr] = self.to_description(character)
        context["fields"] = self.object.fields
        return context

    @classmethod
    def is_control(cls, character):
        """
        Return ``True`` if a character is in the Unicode control category.

        :param character: The character to test.
        :type character: unicode
        :return: ``True`` if the character is a control character.
        :rtype: bool
        """
        return unicodedata.category(character).startswith(("Z", "C"))

    @classmethod
    def is_symbol(cls, character):
        """
        Return ``True`` if a character is in the Unicode symbol category.

        :param character: The character to test.
        :type character: unicode
        :return: ``True`` if the character is a symbol.
        :rtype: bool
        """
        return not unicodedata.category(character).startswith(("L", "N"))

    @classmethod
    def to_description(cls, character):
        """
        Return a string that describes the given symbol character.

        :param character: The symbol to describe.
        :type character: unicode
        :return: The description.
        :rtype: unicode
        """
        try:
            name = unicodedata.name(character).capitalize()
        except ValueError:
            code_point = "U+{:04X}".format(ord(character))
            name = cls.CONTROL_NAMES.get(character, code_point)
        if cls.is_control(character):
            return name
        return u"{:s} ({:s})".format(name, character)


class SimpleFormatCreateView(FormatCreateView):
    """Used to create a new instance of the simple format type."""

    form_list = [
        ("options", SimpleFormatForm),
        ("fields", formset_factory(SimpleFormatFieldForm, formset=SimpleFormatFieldFormSet, can_delete=True,
                                   can_order=True)),
    ]
    templates = {
        "options": "bdr/formats/simple/create_options.html",
        "fields": "bdr/formats/simple/create_fields.html",
    }

    def get_form(self, step=None, data=None, files=None):
        """
        Construct a form for a given ``step``. If no ``step`` is defined, the
        current step will be determined automatically.

        The form will be initialized using the ``data`` argument to pre-fill
        the new form. If needed, instance or queryset (for ``ModelForm`` or
        ``ModelFormSet``) will be added too.

        :param step: The name of the current step.
        :type step: str
        :param data: A dictionary containing request data received from the
                     user.
        :type data: dict of unicode
        :param files: A dictionary containing file data received from the user.
        :type files: dict of str
        :return: The ``Form`` instance for this step.
        :rtype: Form
        """
        form = super(SimpleFormatCreateView, self).get_form(step, data, files)
        if step == "fields" and self.request.POST.get("operation") == "add":
            form.add_extra_form()
        return form

    def done(self, form_list, **kwargs):
        """
        Add the format definition to the repository and redirect to its new
        summary page.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: A redirect response to a view of the format.
        :rtype: HttpResponseRedirect
        """
        options_form, fields_form = form_list
        instance = options_form.save(commit=False)

        instance.entry_point_name = "simple"
        for field, value in options_form.cleaned_metadata.items():
            setattr(instance, field, value)
        instance.fields = [field.cleaned_definition for field in fields_form.ordered_forms]

        instance.save()
        options_form.save_m2m()
        return redirect(instance)


class SimpleFormatEditView(FormatEditView):
    """Used to edit an existing instance of the simple format type."""

    form_list = [
        ("options", SimpleFormatForm),
        ("fields", formset_factory(SimpleFormatFieldForm, formset=SimpleFormatFieldFormSet, can_delete=True,
                                   can_order=True)),
    ]
    model = SimpleFormat
    templates = {
        "options": "bdr/formats/simple/edit_options.html",
        "fields": "bdr/formats/simple/edit_fields.html",
    }

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
        if step == "fields":
            return self.object.fields
        return super(SimpleFormatEditView, self).get_form_initial(step)

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
            return self.object
        return super(SimpleFormatEditView, self).get_form_instance(step)

    def done(self, form_list, **kwargs):
        """
        Modify the format definition and redirect to its summary page.

        :param form_list: A list of the forms presented to the user.
        :type form_list: list of django.forms.Form
        :param kwargs: The keyword arguments extracted from the URL route.
        :type kwargs: dict of str
        :return: A redirect response to a view of the format.
        :rtype: HttpResponseRedirect
        """
        options_form, fields_form = form_list
        if options_form.has_changed() or fields_form.has_changed():
            self.object = options_form.save(commit=False)

            for field, value in options_form.cleaned_metadata.items():
                setattr(self.object, field, value)
            self.object.fields = [field.cleaned_definition for field in fields_form.ordered_forms]

            self.object.save()
            options_form.save_m2m()
        return redirect(self.object)


class SimpleFormatDeleteView(FormatDeleteView):
    """
    This view is used to confirm the deletion of an existing simple format.

    Files and revisions using the deleted format are subsequently marked as
    containing raw data.
    """

    template_name = "bdr/formats/confirm_delete.html"


class SimpleRevisionExportView(RevisionExportView):
    """
    This view streams a compressed file to the client.

    File compression is performed on the fly.
    """

    form_list = [
        ("options", SimpleFormatExportOptionsForm),
        ("fields", formset_factory(SimpleFormatFieldSelectionForm, formset=SimpleFormatFieldSelectionFormSet, extra=0)),
    ]
    model = SimpleRevision
    templates = {
        "options": "bdr/revisions/simple/export_options.html",
        "fields": "bdr/revisions/simple/export_fields.html",
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
        options_form, fields_formset \
            = form_list  # type: SimpleFormatExportOptionsForm, SimpleFormatFieldSelectionFormSet
        field_names = [field["name"] for field in fields_formset.selected]
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
        if step == "fields":
            return self.object.format.fields
        return super(SimpleRevisionExportView, self).get_form_initial(step)

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
        return super(SimpleRevisionExportView, self).get_form_instance(step)
