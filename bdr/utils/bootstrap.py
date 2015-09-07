"""
Augments the Bootstrap 3 Django package to introduce the ability to include
button add-ons in input groups.

This module exports the following classes:

FieldRenderer
    An enhanced form field renderer that can produce button add-ons in input
    groups.
InlineFieldRenderer
    An enhanced version of the form field renderer that outputs inline fields
    and can produce button add-ons in input groups.
"""

from bootstrap3.exceptions import BootstrapError
from bootstrap3.renderers import (
    FieldRenderer as BaseFieldRenderer, InlineFieldRenderer as BaseInlineFieldRenderer
)
from django.forms import TextInput, Select

__all__ = ["FieldRenderer", "InlineFieldRenderer"]
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


# noinspection PyUnresolvedReferences
# This mixin is not intended to be used in a standalone fashion, therefore
# references exist to the properties of the BaseFieldRenderer class.
class ButtonAddonMixin(object):
    """
    A mix-in used to extend a built-in field renderer to support button add-ons
    within input groups, in addition to regular add-ons.

    Button add-ons can be added either before a form control using the
    `button_addon_before` parameter, or afterward using `button_addon_after`.
    They may be defined in two ways, as with regular add-ons: by customising
    the widget of a field, or as an argument to the `bootstrap3_field` tag in a
    template. For more information about widget instance customisation, see the
    discussion in the Django documentation.

    The parameter values are a dictionary with the following keys:

    content
        The content to be rendered within the button.
    type
        (Optional) The type of button: "submit", "button" or "reset"
        (default: "submit").
    name
        (Optional) The control name associated with this button.
    value
        (Optional) For submit type buttons, this is the value sent to the
        server paired with the control name.
    class
        (Optional) The class attribute value for the button
        (default: "btn btn-default").

    A `BootstrapError` exception will be raised if both a button and regular
    add-on is added in the same position on a single field.
    """
    def __init__(self, *args, **kwargs):
        # noinspection PyArgumentList
        # The sibling superclass expects arguments in its __init__ method,
        # therefore we must be prepared to accept them, also.
        super(ButtonAddonMixin, self).__init__(*args, **kwargs)
        self.button_addon_before = kwargs.get("button_addon_before",
                                              self.initial_attrs.pop("button_addon_before", {}))
        """:type: dict"""
        self.button_addon_after = kwargs.get("button_addon_after",
                                             self.initial_attrs.pop("button_addon_after", {}))

        # Remove the add-on specifications so that they aren't rendered out.
        if "addon_before" in self.widget.attrs:
            del self.widget.attrs["addon_before"]
        if "addon_after" in self.widget.attrs:
            del self.widget.attrs["addon_after"]
        if "button_addon_before" in self.widget.attrs:
            del self.widget.attrs["button_addon_before"]
        if "button_addon_after" in self.widget.attrs:
            del self.widget.attrs["button_addon_after"]

        if ((self.addon_before and self.button_addon_before) or
                (self.addon_after and self.button_addon_after)):
            raise BootstrapError("Cannot have more than one add-on {0} a form control.".format(
                "before" if self.addon_before else "after"))

    def make_input_group(self, html):
        """
        Constructs an input group that wraps the given `html` string.

        If the widget for the field is not a `Select` or `TextInput` type, the
        `html` string is returned unmodified.

        :param html: A HTML string to be inserted into an input group.
        :type html: str
        :return: An input group.
        :rtype: str
        """
        if isinstance(self.widget, (TextInput, Select)):
            before = self.make_addon(self.addon_before or self.button_addon_before)
            after = self.make_addon(self.addon_after or self.button_addon_after)

            if before or after:
                html = ('<div class="input-group">'
                        '{before}{html}{after}'
                        '</div>').format(before=before, after=after, html=html)
        return html

    @classmethod
    def make_addon(cls, addon):
        """
        Creates an addon that can be inserted into an input group.

        :param addon: A string defining the content of a regular addon, or a
                      dictionary that describes the attributes of a button
                      addon.
        :type addon: dict or str
        :return: An addon for an input group.
        :rtype: str
        :raise KeyError: if a dictionary is given without a `content` key.
        """
        addon_type = "addon"
        if addon and isinstance(addon, dict):
            addon.setdefault("type", "submit")
            addon.setdefault("class", "btn btn-default")
            content = addon["content"]

            attributes = {attribute: ' {attr}="{value}"'.format(attr=attribute, value=value)
                          for attribute, value in addon.items() if attribute != "content"}
            attributes.setdefault("name", "")
            attributes.setdefault("value", "")

            addon = '<button{type}{name}{value}{class}>{content}</button>'.format(content=content,
                                                                                  **attributes)
            addon_type = "btn"

        if addon:
            return '<span class="input-group-{type}">{addon}</span>'.format(addon=addon,
                                                                            type=addon_type)
        return ""


class FieldRenderer(ButtonAddonMixin, BaseFieldRenderer):
    """
    An enhanced form field renderer that can produce button add-ons in input
    groups.

    Button add-ons can be added either before a form control using the
    `button_addon_before` parameter, or afterward using `button_addon_after`.
    They may be defined in two ways, as with regular add-ons: by customising
    the widget of a field, or as an argument to the `bootstrap3_field` tag in a
    template. For more information about widget instance customisation, see the
    discussion in the Django documentation.

    The parameter values are a dictionary with the following keys:

    content
        The content to be rendered within the button.
    type
        (Optional) The type of button: "submit", "button" or "reset"
        (default: "submit").
    name
        (Optional) The control name associated with this button.
    value
        (Optional) For submit type buttons, this is the value sent to the
        server paired with the control name.
    class
        (Optional) The class attribute value for the button
        (default: "btn btn-default").

    A `BootstrapError` exception will be raised if both a button and regular
    add-on is added in the same position on a single field.
    """

    pass


class InlineFieldRenderer(ButtonAddonMixin, BaseInlineFieldRenderer):
    """
    An enhanced inline form field renderer that can produce button add-ons in
    input groups.

    Button add-ons can be added either before a form control using the
    `button_addon_before` parameter, or afterward using `button_addon_after`.
    They may be defined in two ways, as with regular add-ons: by customising
    the widget of a field, or as an argument to the `bootstrap3_field` tag in a
    template. For more information about widget instance customisation, see the
    discussion in the Django documentation.

    The parameter values are a dictionary with the following keys:

    content
        The content to be rendered within the button.
    type
        (Optional) The type of button: "submit", "button" or "reset"
        (default: "submit").
    name
        (Optional) The control name associated with this button.
    value
        (Optional) For submit type buttons, this is the value sent to the
        server paired with the control name.
    class
        (Optional) The class attribute value for the button
        (default: "btn btn-default").

    A `BootstrapError` exception will be raised if both a button and regular
    add-on is added in the same position on a single field.
    """

    pass
