"""
This module defines customised fields for use with forms in this application.
"""

from django.core.exceptions import ValidationError
from django.forms.fields import BooleanField, CharField, MultiValueField

from .widgets import SelectableTextInput

__all__ = []
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


class SelectableCharField(MultiValueField):
    """
    This field combines a text box with a checkbox to create an optional
    input.

    If the associated checkbox is deselected when the form is submitted, the
    textbox value is ignored and evaluates to `None`.
    """

    field_classes = (BooleanField, CharField)
    widget = SelectableTextInput

    def __init__(self, *args, **kwargs):
        fields = [field() if isinstance(field, type) else field
                  for field in self.field_classes]
        super(SelectableCharField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        """
        Return a single value to represent the given list of values.

        :param data_list: A list of values from each component field.
        :type data_list: list
        :return: A single value that represents the combined value of this
                 field.
        :rtype: unicode | None
        """
        if data_list[0]:
            value = data_list[1]
            if value in self.empty_values:
                raise ValidationError(self.error_messages["invalid"])
            return value
        return None
