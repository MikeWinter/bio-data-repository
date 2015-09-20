"""
This module defines the forms used to manipulate data descriptors managed by
the repository.

This following classes are exported:

    CategoryForm
    DatasetForm
    FileForm
    TagForm
    SearchForm
    UploadForm
"""

from django.forms import Form, ModelForm
from django.forms.fields import CharField, FileField
from django.forms.widgets import FileInput, HiddenInput, Textarea, TextInput
from django.core.urlresolvers import reverse_lazy

from .fields import SelectableCharField
from ..models import Category, Dataset, File, Tag

__all__ = ["CategoryForm", "DatasetForm", "FileForm", "TagForm", "SearchForm", "UploadForm"]
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

    # def clean_default_format(self):
    #     value = self.cleaned_data.get('default_format', None)
    #     if value is None:
    #         ValidationError(self.fields['default_format'].error_messages['required'],
    #                         code='required')
    #     return value

    class Meta(object):
        """Configuration options for the file form."""

        model = File
        fields = "__all__"


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

    def __init__(self, *args, **kwargs):
        super(FileContentSelectionForm, self).__init__(*args, **kwargs)
        self.fields["mapped_name"].label = self.initial["real_name"]
