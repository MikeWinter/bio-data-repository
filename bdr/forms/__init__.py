"""
This module defines the forms used to manipulate data descriptors managed by
the repository.

This following classes are exported:

    CategoryForm
    DatasetForm
    FileForm
    FilterForm
    SourceForm
    TagForm
    SearchForm
    UploadForm
"""

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.forms import CharField, FileField, ModelChoiceField
from django.forms import FileInput, HiddenInput, Textarea, TextInput
from django.forms import Form, ModelForm

from .fields import SelectableCharField
from .widgets import ComboTextInput, ScaledNumberInput
from ..models import Category, Dataset, File, Filter, Format, Revision, Source, Tag

__all__ = ["CategoryForm", "DatasetForm", "FileForm", "FilterForm", "SourceForm", "TagForm",
           "SearchForm", "UploadForm"]
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


class CategoryForm(ModelForm):
    """
    Displays the properties of a category to facilitate creating new, and
    editing existing, entries.
    """

    class Meta(object):
        """Configuration options for the category form."""

        model = Category
        fields = "__all__"


class DatasetForm(ModelForm):
    """
    Displays the properties of a dataset to facilitate creating new, and
    editing existing, entries.
    """

    class Meta(object):
        """Configuration options for the dataset form."""

        model = Dataset
        fields = "__all__"
        widgets = {
            "notes": Textarea(attrs=dict(rows=6))
        }


class FileForm(ModelForm):
    """
    Displays the properties of a file to facilitate creating new, and
    editing existing, entries.
    """

    class Meta(object):
        """Configuration options for the file form."""

        model = File
        fields = "__all__"


class FilterForm(ModelForm):
    """
    Displays the properties of a filter to facilitate creating new, and
    editing existing, entries.
    """

    class Media(object):
        """
        Declares resources that should be included when this form is displayed.
        """

        js = ("bdr/js/filter-test.js",)

    class Meta(object):
        """Configuration options for the filter form."""

        model = Filter
        fields = "__all__"


class RevisionForm(ModelForm):
    """
    Displays the properties of a revision to facilitate editing existing
    entries.
    """

    class Meta(object):
        """Configuration options for the revision form."""

        model = Revision
        fields = "__all__"


class SourceForm(ModelForm):
    """
    Displays the properties of a source to facilitate creating new, and
    editing existing, entries.
    """

    class Meta(object):
        """Configuration options for the source form."""

        model = Source
        fields = "__all__"
        widgets = {
            "period": ScaledNumberInput([(1, "hours"), (24, "days"), (168, "weeks")], default=1)
        }


class TagForm(ModelForm):
    """
    Displays the properties of a tag to facilitate creating new, and
    editing existing, entries.
    """

    class Meta(object):
        """Configuration options for the tag form."""

        model = Tag
        fields = "__all__"
        widgets = {
            "name": TextInput(attrs=dict(addon_before="#"))
        }


class SearchForm(Form):
    """
    Provides a text box and submission button for searching for entities by
    name and tag.
    """

    query = CharField(
        label="",
        widget=TextInput(
            dict(type="search", placeholder="Search the repository...", button_addon_after={
                "content": '<span class="glyphicon glyphicon-search" aria-hidden="true"></span>'
                           '<span class="sr-only">Search</span>'})))

    class Media(object):
        """
        Declares resources that should be included when this form is displayed.
        """

        js = ("//cdnjs.cloudflare.com/ajax/libs/typeahead.js/0.11.1/typeahead.bundle.min.js",
              reverse_lazy("bdr:search.js"))


class UploadForm(Form):
    """
    Provides a file selection box and submission button for uploading a file.
    """

    file = FileField(widget=FileInput({"class": "form-control"}))


class FileContentSelectionForm(Form):
    """
    Enables a user to choose whether a file is added to the repository, and
    what its name should be.
    """

    real_name = CharField(widget=HiddenInput)
    mapped_name = SelectableCharField(required=False,
                                      error_messages={"invalid": "Enter a file name."})
    format = ModelChoiceField(Format.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super(FileContentSelectionForm, self).__init__(*args, **kwargs)
        self.fields["mapped_name"].label = self.initial["real_name"]

    def clean(self):
        """
        Validate the form.

        In particular, this method asserts that if a file is selected, its
        format has also been set.
        """
        cleaned_data = super(FileContentSelectionForm, self).clean()
        if cleaned_data["mapped_name"] is not None and cleaned_data["format"] is None:
            raise ValidationError("A format must be specified for a file to be added to the repository.")
        return cleaned_data
