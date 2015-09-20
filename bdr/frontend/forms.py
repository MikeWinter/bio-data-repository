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

from django.forms import fields, widgets
from django.forms.models import ModelForm

from . import models
from .widgets import ComboTextInput


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


class FormatFieldSelectionForm(ModelForm):
    selected = fields.BooleanField(initial=False, required=False)

    class Meta(object):
        model = models.FormatField
        exclude = ['format', 'ordinal']
        widgets = {'name': widgets.HiddenInput(),
                   'is_key': widgets.HiddenInput()}
