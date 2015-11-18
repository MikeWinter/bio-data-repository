"""
This module defines forms and formsets used to interact with formats of the
simple type.
"""

from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm, CharField, BooleanField, HiddenInput
from django.forms.formsets import BaseFormSet, TOTAL_FORM_COUNT

from ...forms import ComboTextInput
from ...models.simple import SimpleFormat

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


class SimpleFormatForm(ModelForm):
    """
    Presents the user with lists of common options used in simple formats as
    well as the ability to specify customised values.
    """

    COMMENT_DEFAULT = "#"
    COMMENT_CHOICES = [("#", "Hash (#)"), (";", "Semicolon (;)"), ("None", "None"), ("", "Other:")]
    ESCAPE_DEFAULT = "\\"
    ESCAPE_CHOICES = [("\\", "Backslash (\\)"), ("None", "None"), ("", "Other:")]
    QUOTE_DEFAULT = "\""
    QUOTE_CHOICES = [("\"", "Quotation mark (\")"), ("'", "Apostrophe (')"), ("|", "Pipe (|)"), ("None", "None"),
                     ("", "Other:")]
    SEPARATOR_DEFAULT = ","
    SEPARATOR_CHOICES = [("\t", "Tab"), (" ", "Space"), (",", "Comma (,)"), (";", "Semicolon (;)"), ("|", "Pipe (|)"),
                         ("", "Other:")]

    separator = CharField(max_length=1,
                          widget=ComboTextInput(choices=SEPARATOR_CHOICES, default=SEPARATOR_DEFAULT),
                          help_text="Used to separate fields in a record.")
    comment = CharField(max_length=1, required=False,
                        widget=ComboTextInput(choices=COMMENT_CHOICES, default=COMMENT_DEFAULT),
                        help_text="Used to mark a line as a comment.")
    quote = CharField(max_length=1, required=False,
                      widget=ComboTextInput(choices=QUOTE_CHOICES, default=QUOTE_DEFAULT),
                      help_text="If fields may contain special characters, select the character used to quote those"
                                " values.")
    escape = CharField(max_length=1, required=False,
                       widget=ComboTextInput(choices=ESCAPE_CHOICES, default=ESCAPE_DEFAULT),
                       help_text="If quotes are not used, select the character used to escape special characters. If"
                                 " quotes are used and no escape character is chosen, embedded quotes are doubled (for"
                                 " example, \"It's a test!\" would be saved as 'It''s a test!' when using single"
                                 " quotes).")

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance")
        initial = kwargs.pop("initial", None)
        if instance is not None:
            # Computed properties drawn from the metadata format field are not
            # initialised at the same time as other fields as they are opaque
            # to ModelForm. They are initialised here instead.
            initial = initial or {}
            for field in ["separator", "comment", "quote", "escape"]:
                initial[field] = getattr(instance, field)
        super(SimpleFormatForm, self).__init__(*args, instance=instance, initial=initial, **kwargs)

    @property
    def cleaned_metadata(self):
        """
        Validated options that describe the properties of simple formatted
        data.
        """
        if self.is_valid():
            return {key: value for key, value in self.cleaned_data.items() if key not in ["name"]}
        raise AttributeError("'{:s}' object has no attribute 'cleaned_metadata'".format(self.__class__.__name__))

    class Meta(object):
        """Configuration options for the format options form."""

        model = SimpleFormat
        fields = "__all__"


class SimpleFormatExportOptionsForm(SimpleFormatForm):
    """
    Presents the user with common options used to export simple formatted data.
    """

    TERMINATOR_DEFAULT = "LF"
    TERMINATOR_CHOICES = [("LF", "Linux (LF)"), ("CRLF", "Windows (CRLF)"), ("CR", "Mac (CR)"), ("", "Other:")]
    TERMINATOR_CHARACTER_MAP = {
        "LF": "\n",
        "CRLF": "\r\n",
        "CR": "\r"
    }

    line_terminator = CharField(widget=ComboTextInput(choices=TERMINATOR_CHOICES, default=TERMINATOR_DEFAULT),
                                help_text="Used to separate records.")

    @property
    def cleaned_metadata(self):
        """Validated options for exporting simple formatted data."""
        metadata = super(SimpleFormatExportOptionsForm, self).cleaned_metadata
        if metadata["line_terminator"] in self.TERMINATOR_CHARACTER_MAP:
            metadata["line_terminator"] = self.TERMINATOR_CHARACTER_MAP[metadata["line_terminator"]]
        return metadata

    class Meta(SimpleFormatForm.Meta):
        """Configuration options for the export options form."""

        exclude = ["name"]


class SimpleFormatFieldForm(Form):
    """
    Displays the properties of simple form fields.
    """

    name = CharField()
    is_key = BooleanField(required=False)

    @property
    def cleaned_definition(self):
        """The validated definition of a simple format field."""
        if self.is_valid():
            return {key: value for key, value in self.cleaned_data.items() if key in ["name", "is_key"]}
        raise AttributeError("'{:s}' object has no attribute 'cleaned_definition'".format(self.__class__.__name__))


class SimpleFormatFieldSelectionForm(Form):
    """
    Enables the user to select a field from among those defined in a simple
    format.
    """

    selected = BooleanField(initial=False, required=False)
    name = CharField(required=False, widget=HiddenInput)
    is_key = BooleanField(required=False, widget=HiddenInput)


class SimpleFormatFieldFormSet(BaseFormSet):
    """
    Each form in this set represents a field definition in a simple format
    type.
    """

    def __init__(self, *args, **kwargs):
        super(SimpleFormatFieldFormSet, self).__init__(*args, **kwargs)
        self.data = self.data.copy()
        self.reevaluate = False

    def add_extra_form(self):
        """Add a blank form to the set and force re-rendering."""
        field_name = self.add_prefix(TOTAL_FORM_COUNT)
        self.data[field_name] = int(self.data[field_name]) + 1
        self.reevaluate = True

    def is_valid(self):
        """Return ``True`` if every form in this set is valid."""
        return False if self.reevaluate else super(SimpleFormatFieldFormSet, self).is_valid()


class SimpleFormatFieldSelectionFormSet(BaseFormSet):
    """
    Enables the user to select a field from among the set defined in a simple
    format.
    """

    def clean(self):
        """
        Validate the formset as a whole.

        At least one field must be selected, otherwise this method will raise
        an exception.

        :raises ValidationError: If no fields are selected.
        """
        for form in self.forms:
            if form.cleaned_data["selected"]:
                return super(SimpleFormatFieldSelectionFormSet, self).clean()
        raise ValidationError("At least one field must be selected.")

    @property
    def selected(self):
        """The fields selected by the user."""
        return [item for item in self.cleaned_data if item['selected']]
