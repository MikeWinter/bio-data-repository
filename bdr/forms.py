from django.forms import Form, ModelForm
from django.forms.fields import BooleanField, CharField
from django.forms.widgets import TextInput
from django.core.urlresolvers import reverse_lazy

from .models import Category

__all__ = ["CategoryForm", "CategoryDeletionForm", "SearchForm"]
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
    class Meta(object):
        model = Category
        fields = "__all__"


class CategoryDeletionForm(Form):
    delete = BooleanField(label="Confirm deletion",
                          help_text="Are you sure you want to delete this category?")


class SearchForm(Form):
    query = CharField(
        label="",
        widget=TextInput(
            attrs=dict(placeholder="Search the repository...", button_addon_after={
                "content": '<span class="glyphicon glyphicon-search" aria-hidden="true"></span>'
                           '<span class="sr-only">Search</span>'})))

    class Media(object):
        js = ("//cdnjs.cloudflare.com/ajax/libs/typeahead.js/0.11.1/typeahead.bundle.min.js",
              reverse_lazy("bdr:search.js"))
