"""
This module defines customised widgets for use with forms in this application.
"""

from django.forms.widgets import CheckboxInput, MultiWidget, TextInput

__all__ = []
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
