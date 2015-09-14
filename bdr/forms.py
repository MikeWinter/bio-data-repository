"""
This module defines the forms used to manipulate data descriptors managed by
the repository.

This following classes are exported:

    CategoryForm
    DatasetForm
    TagForm
    SearchForm
"""

from django.forms import Form, ModelForm
from django.forms.fields import CharField
from django.forms.widgets import Textarea, TextInput
from django.core.urlresolvers import reverse_lazy

from .models import Category, Dataset, Tag

__all__ = ["CategoryForm", "DatasetForm", "TagForm", "SearchForm"]
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
    editing existing, categories.
    """

    class Meta(object):
        """Configuration options for the category form."""

        model = Category
        fields = "__all__"


class DatasetForm(ModelForm):
    """
    Displays the properties of a category to facilitate creating new, and
    editing existing, datasets.
    """

    class Meta(object):
        """Configuration options for the dataset form."""

        model = Dataset
        fields = "__all__"
        widgets = {
            "notes": Textarea(attrs=dict(rows=6))
        }


class TagForm(ModelForm):
    """
    Displays the properties of a category to facilitate creating new, and
    editing existing, tags.
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
            attrs=dict(type="search", placeholder="Search the repository...", button_addon_after={
                "content": '<span class="glyphicon glyphicon-search" aria-hidden="true"></span>'
                           '<span class="sr-only">Search</span>'})))

    class Media(object):
        """
        Declares resources that should be included when this form is displayed.
        """

        js = ("//cdnjs.cloudflare.com/ajax/libs/typeahead.js/0.11.1/typeahead.bundle.min.js",
              reverse_lazy("bdr:search.js"))
