"""
This module defines customised widgets for use with forms in this application.
"""

from django.forms.widgets import CheckboxInput, MultiWidget, Select, TextInput

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


# noinspection PyAbstractClass
# The render method is not abstract.
class SelectableTextInput(MultiWidget):
    """
    This widget combines a text box with a checkbox to create an optional
    input.

    If the associated checkbox is deselected when the form is submitted, the
    textbox value is ignored.

    This widget is intended to be used with the Bootstrap CSS framework. The
    two controls are rendered as an input group with the checkbox integrated in
    the `:before` position (typically the left-hand side of the text box).
    """

    selection_widget = CheckboxInput
    value_widget = TextInput

    def __init__(self, attrs=None):
        super(SelectableTextInput, self).__init__([self.selection_widget, self.value_widget], attrs)

    def decompress(self, value):
        """
        Return a list of decompressed values for the given compressed value.

        The first element is the state of the checkbox. The second element is
        the value of the text box; this will be `None` if the checkbox was
        deselected.

        :param value: A compressed value to be represented by this widget.
        :type value: str | unicode
        :return: The decompressed interpretation of the value.
        :rtype: list of (bool, str | unicode)
        """
        if value:
            return [True, value]
        return [False, None]

    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), returns a Unicode string
        representing the HTML for the whole lot.

        This hook allows you to format the HTML design of the widgets, if
        needed.

        :param rendered_widgets: A list of widgets rendered in HTML.
        :type rendered_widgets: list of unicode
        :return: A HTML string combining each widget.
        :rtype: unicode
        """

        return """
        <div class="input-group">
            <span class="input-group-addon">{0}</span>
            {1}
        </div>
        """.format(*rendered_widgets)


# noinspection PyAbstractClass
# Base class implements the render method
class ComboTextInput(MultiWidget):
    """
    This widget combines a select menu with a text box to create a list of
    suggested values and the ability to define a custom value.

    This widget is intended to be used with the Bootstrap CSS framework.
    """

    def __init__(self, choices, default="", attrs=None):
        if attrs is None:
            attrs = {}
        attrs["data-type"] = "combobox"
        self._choices = choices
        self._default = default
        super(ComboTextInput, self).__init__([Select(choices=self._choices), TextInput], attrs)

    def decompress(self, value):
        """
        Return a list of decompressed values for the given compressed value.

        The first element is the selected, suggested value. The second element
        is the customised value.

        :param value: A compressed value to be represented by this widget.
        :type value: str | unicode
        :return: The decompressed interpretation of the value.
        :rtype: list of (bool, str | unicode)
        """
        if value is None:
            return [self._default, ""]
        if value == "":
            return ["None", ""]
        for val, txt in self._choices:
            if value == val:
                return [value, ""]
        return ["", value]

    def value_from_datadict(self, data, files, name):
        """
        Return the value of this widget derived from the submitted data
        dictionaries.

        :param data: A dictionary of strings submitted by the user via a form.
        :type data: dict of (str | unicode)
        :param files: A dictionary of files uploaded by the user.
        :type files: dict of str
        :param name: The key name of this widget.
        :type name: str
        :return: The value of this widget.
        :rtype: str | unicode
        """
        suggested, custom = super(ComboTextInput, self).value_from_datadict(data, files, name)
        value = suggested if suggested != "" else custom
        return value if value != "None" else None

    class Media(object):
        """
        Declares resources that should be included when this form is displayed.
        """

        js = ("bdr/js/combo.js",)
