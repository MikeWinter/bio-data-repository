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

from django import forms

from . import models


class Choice(forms.Select):
    def __init__(self, attrs=None, choices=(), field_name=None):
        super(Choice, self).__init__(attrs, choices)
        self._field_name = field_name

    def value_from_datadict(self, data, files, name):
        value = super(Choice, self).value_from_datadict(data, files, name)
        if value is None:
            return None
        return value.split('/')[-1]


class MultipleChoice(forms.SelectMultiple):
    def __init__(self, attrs=None, choices=(), field_name=None):
        super(MultipleChoice, self).__init__(attrs, choices)
        self._field_name = field_name

    def value_from_datadict(self, data, files, name):
        value = super(MultipleChoice, self).value_from_datadict(data, files, name)
        if value is None:
            return None
        if isinstance(value, dict):
            return [elem[self._field_name] for elem in value]
        else:
            return [href.split('/')[-1] for href in value]


class CategoryForm(forms.ModelForm):
    class Meta(object):
        model = models.Category
        exclude = ('parent',)


class TagForm(forms.ModelForm):
    class Meta(object):
        model = models.Tag
        fields = ['name']


class DatasetForm(forms.ModelForm):
    def formfield_callback(model_field, **kwargs):
        form_field = model_field.formfield(**kwargs)
        if model_field.name == 'categories':
            form_field.to_field_name = 'slug'
        elif model_field.name == 'tags':
            form_field.to_field_name = 'pk'
        return form_field

    class Meta(object):
        model = models.Dataset
        exclude = ('updated_at',)
        widgets = {
            'categories': MultipleChoice(field_name='slug'),
            'tags': MultipleChoice(field_name='pk')
        }


class FileForm(forms.ModelForm):
    def formfield_callback(model_field, **kwargs):
        form_field = model_field.formfield(**kwargs)
        if model_field.name == 'default_format':
            form_field.to_field_name = 'slug'
        elif model_field.name == 'tags':
            form_field.to_field_name = 'pk'
        return form_field

    class Meta(object):
        model = models.File
        fields = '__all__'
        widgets = {
            'default_format': Choice(field_name='slug'),
            'tags': MultipleChoice(field_name='pk')
        }


class RevisionForm(forms.ModelForm):
    def formfield_callback(model_field, **kwargs):
        form_field = model_field.formfield(**kwargs)
        if model_field.name == 'tags':
            form_field.to_field_name = 'pk'
        return form_field

    class Meta(object):
        model = models.Revision
        fields = '__all__'
        widgets = {
            'tags': MultipleChoice(field_name='pk')
        }