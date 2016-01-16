"""
This module contains class definitions for proxy models relating to simple type
formats.
"""

from .base import Format, Revision

__all__ = ["SimpleFormat", "SimpleRevision"]
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


class DrugBank43Format(Format):
    """
    Represents an instance of a DrugBank 4.3 format for files stored in the
    repository.

    This class overrides the :py:meth:`~Format.reader` and
    :py:meth:`~Format.converter` methods of the :py:class:`Format` class.
    """

    def converter(self, reader, field_names, **kwargs):
        """
        Return a :py:class:`Converter` over the given format reader.

        :param reader: A format reader.
        :type reader: Reader
        :param field_names: An iterable that contains the names of fields to be
                            read from ``reader``.
        :type field_names: list of str | tuple of str
        :param kwargs: Additional format-dependent arguments for initialising
                       the converter.
        :type kwargs: dict of str
        :return: A suitable ``Converter`` instance.
        :rtype: bdr.formats.Converter
        :raise ImportError: if this format does not have an associated
                            ``Converter`` class.
        """

        from bdr.formats.drugbank43.parser import Converter
        return Converter(reader, field_names, **kwargs)

    class Meta(object):
        """Metadata options for the ``DrugBank43Format`` model class."""

        proxy = True


class DrugBank43Revision(Revision):
    """
    Represents revisions of files maintained by this repository that use a
    DrugBank 4.3 format type.
    """

    @property
    def format(self):
        """The format of this revision."""
        if self._format.entry_point_name != "drugbank43":
            raise TypeError("Not a DrugBank 4.3 format type")
        return DrugBank43Format.objects.get(pk=self._format.pk)

    class Meta(object):
        """Metadata options for the ``DrugBank43Revision`` model class."""

        proxy = True
