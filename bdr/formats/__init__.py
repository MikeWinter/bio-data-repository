"""
The base types for parsing and rewriting dataset file formats.
"""
# TODO: Document format plug-in mechanism

from collections import Iterable, Mapping
import operator

import pkg_resources

__all__ = ["Record", "Reader", "Writer"]
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

_ENTRY_POINT_GROUP_NAME = "bdr.formats"


def get_entry_point(name):
    """
    Return the entry point of the format with the given name.

    :param name: The name of the format whose entry point is to be returned.
    :type name: str
    :return: The entry point of the named format.
    :rtype: module
    """
    entry_points = list(pkg_resources.iter_entry_points(_ENTRY_POINT_GROUP_NAME, name))
    return entry_points.pop().load()


def get_realisable_formats():
    """
    Return a list of format types that can be instantiated and customised by
    the user.

    :return: A list of customisable format types.
    :rtype: list of module
    """
    formats = []
    for entry_point in pkg_resources.iter_entry_points(_ENTRY_POINT_GROUP_NAME):
        module = entry_point.load()
        if "create" in module.views:
            module.entry_point_name = entry_point.name
            formats.append(module)
    return sorted(formats, key=operator.attrgetter("name"))


class Record(Mapping):
    """
    Represents a record within a data file, composed of one or more fields.

    By default, records serialise to a comma-separated string.
    """

    def __init__(self):
        self._data = {}
        self._fields = []

    @property
    def fields(self):
        """
        The list of fields contained in this record.
        """
        return self._fields

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self.fields)

    def __len__(self):
        return len(self.fields)

    def __contains__(self, item):
        return item in self.fields

    def __str__(self):
        return ','.join(map(lambda field: str(self._data[field]), self.fields))


class Reader(Iterable):
    """
    Responsible for parsing files into discrete records.

    Instances of this type are iterable, returning records in file order.
    """

    def __init__(self, stream, metadata=""):
        """
        :type stream: io.BufferedIOBase | io.RawIOBase
        :param metadata: str
        """
        self._stream = stream
        self._metadata = metadata

    def read(self):
        """
        Read a record from the stream wrapped by this reader.

        :return: The read record.
        :rtype: Record
        """
        for record in self:
            yield record

    def __iter__(self):
        """
        :rtype: Record
        """
        raise NotImplementedError


class Writer(object):
    """
    Responsible for writing out records according to format-defined rules, yielding only the specified fields.

    Instances of this type are iterable, returning converted records in file order.
    """

    def __init__(self, stream, metadata="", fields=None):
        """
        :type stream: io.BufferedIOBase | io.RawIOBase
        :param metadata: str
        :param fields: list of str | None
        """
        self._stream = stream
        self._metadata = metadata
        self._fields = fields or []

    def write(self, record):
        """
        Write the given record to the output stream wrapped by this writer.

        :param record: The record to write.
        :type record: Record
        """
        self._stream.write(str(record))
