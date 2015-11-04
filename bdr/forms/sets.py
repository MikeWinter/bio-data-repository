"""
This module defines formsets used to manipulate groups of forms used while
making changes to the data descriptors managed by the repository.
"""

from django.core.exceptions import ValidationError
from django.forms.formsets import formset_factory, BaseFormSet, TOTAL_FORM_COUNT

from . import SimpleFormatFieldForm

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


class FileContentSelectionFormSet(BaseFormSet):
    """
    Each form in this set represents a member of an archive that can either be
    chosen for inclusion in the repository, or skipped.

    Each chosen file can be optionally renamed prior to submission.
    """

    def clean(self):
        """
        Validate the formset as a whole.

        At least one file member must be selected, otherwise this method will
        raise an exception.

        :raises ValidationError: If no file members are selected.
        """
        for form in self.forms:
            if form not in self.deleted_forms and form.cleaned_data["mapped_name"] is not None:
                break
        else:
            raise ValidationError("No files selected.")


class SimpleFormatFieldFormSet(formset_factory(SimpleFormatFieldForm, extra=3, can_delete=True)):
    """
    Each form in this set represents a field definition in a simple format
    type.
    """

    def __init__(self, *args, **kwargs):
        super(SimpleFormatFieldFormSet, self).__init__(*args, **kwargs)
        self.data = self.data.copy()

    def add_extra_form(self):
        field_name = self.add_prefix(TOTAL_FORM_COUNT)
        self.data[field_name] = int(self.data[field_name]) + 1
