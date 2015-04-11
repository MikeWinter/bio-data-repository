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

from django.core.exceptions import ValidationError
from django.forms import fields, forms, widgets
from django.forms.models import ModelForm

from . import models
from .widgets import AnnotatedNumberInput, ComboTextInput


class ArchiveMemberForm(forms.Form):
    name = fields.CharField(widget=widgets.HiddenInput())
    selected = fields.BooleanField(initial=False, required=False)


class CategoryForm(ModelForm):
    class Meta(object):
        model = models.Category
        fields = ['name', 'slug']
        widgets = {'name': widgets.TextInput(attrs={'class': 'form-control'}),
                   'slug': widgets.TextInput(attrs={'class': 'form-control'}),
                   'parent': widgets.Select(attrs={'class': 'form-control'})}


class FileEditForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(FileEditForm, self).__init__(*args, **kwargs)
        self.empty_permitted = False

    def clean_default_format(self):
        value = self.cleaned_data.get('default_format', None)
        if value is None:
            ValidationError(self.fields['default_format'].error_messages['required'], code='required')
        return value

    class Meta(object):
        model = models.File
        fields = ['default_format', 'tags', 'name', 'dataset']
        widgets = {'name': widgets.HiddenInput(),
                   'dataset': widgets.HiddenInput(),
                   'default_format': widgets.Select(attrs={'class': 'form-control'}),
                   'tags': widgets.SelectMultiple(attrs={'class': 'form-control'})}


class FileUploadForm(forms.Form):
    new_file = fields.FileField(allow_empty_file=False,
                                widget=widgets.FileInput(attrs={'class': 'form-control'}))


class FormatForm(ModelForm):
    _comment_choices = [('#', 'Hash (#)'), (';', 'Semicolon (;)'), ('None', 'None'), ('', 'Other:')]
    _quote_choices = [('"', 'Quotation mark (")'), ('\'', 'Apostrophe (\')'), ('|', 'Pipe (|)'), ('None', 'None'),
                      ('', 'Other:')]
    _separator_choices = [('\t', 'Tab'), (' ', 'Space'), (',', 'Comma (,)'), (';', 'Semicolon (;)'), ('|', 'Pipe (|)'),
                          ('', 'Other:')]
    separator = fields.CharField(widget=ComboTextInput(choices=_separator_choices, default=',',
                                                       attrs={'class': 'form-control'}))
    quote = fields.CharField(required=False, widget=ComboTextInput(choices=_quote_choices, default='"',
                                                                   attrs={'class': 'form-control'}))
    comment = fields.CharField(required=False, widget=ComboTextInput(choices=_comment_choices, default='#',
                                                                     attrs={'class': 'form-control'}))

    class Meta(object):
        model = models.Format
        exclude = ['readonly']
        widgets = {'name': widgets.TextInput(attrs={'class': 'form-control'}),
                   'slug': widgets.TextInput(attrs={'class': 'form-control'}),
                   'module': widgets.HiddenInput()}


class FormatFieldForm(ModelForm):
    class Meta(object):
        model = models.FormatField
        exclude = ['ordinal']
        widgets = {'name': widgets.TextInput(attrs={'class': 'form-control'})}


class TagForm(ModelForm):
    class Meta(object):
        model = models.Tag
        fields = ['name']
        widgets = {'name': widgets.TextInput(attrs={'class': 'form-control'})}


class DatasetForm(ModelForm):
    class Meta(object):
        model = models.Dataset
        fields = ['name', 'slug', 'categories', 'tags', 'notes', 'update_uri', 'update_username', 'update_password',
                  'update_frequency']
        labels = {'update_uri': 'Update source',
                  'update_username': 'User name',
                  'update_password': 'Password'}
        widgets = {'name': widgets.TextInput(attrs={'class': 'form-control'}),
                   'slug': widgets.TextInput(attrs={'class': 'form-control'}),
                   'categories': widgets.SelectMultiple(attrs={'class': 'form-control'}),
                   'tags': widgets.SelectMultiple(attrs={'class': 'form-control'}),
                   'notes': widgets.Textarea(attrs={'class': 'form-control'}),
                   'update_uri': widgets.URLInput(attrs={'class': 'form-control',
                                                         'placeholder': 'http://example.com/file'}),
                   'update_username': widgets.TextInput(attrs={'class': 'form-control'}),
                   'update_password': widgets.PasswordInput(attrs={'class': 'form-control'}),
                   'update_frequency': AnnotatedNumberInput(attrs={'class': 'form-control'},
                                                            suffix={'text': 'minutes'})}


class FormatFieldSelectionForm(ModelForm):
    selected = fields.BooleanField(initial=False, required=False)

    class Meta(object):
        model = models.FormatField
        exclude = ['format', 'ordinal']
        widgets = {'name': widgets.HiddenInput(),
                   'is_key': widgets.HiddenInput()}