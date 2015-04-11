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

import collections
import importlib


class Record(object):
    """
    Represents a record within a data file, composed of one or more fields.

    By default, records serialise to a comma-separated string.
    """
    _fields = []

    def __init__(self):
        self._data = {}

    def get(self, field):
        """
        Return the value of the field with the name specified by `field`.

        :param field: The name of the field to retrieve.
        :type field:  str
        :return: The value of the specified field.
        :rtype:  str
        :raises KeyError: if the named field does not exist.
        """
        return self._data[field]

    @property
    def fields(self):
        """
        The list of fields contained in this record.
        """
        return self._fields

    def __str__(self):
        return ','.join(map(lambda field: str(self._data[field]), self.fields))


class Reader(collections.Iterable):
    """
    Responsible for parsing files into discrete records.

    Instances of this type are iterable, returning records in file order.
    """
    @classmethod
    def instance(cls, file_, format_):
        """
        Return an instance capable of reading the specified format.

        :param file_: A file-like object to be read.
        :type file_:  file
        :param format_: The format definition used to parse the specified file.
        :type format_: bdr.backend.models.Format
        :return: A file reader.
        :rtype:  Reader
        """
        return _get_type(format_.module, cls.__name__)(file_, format_)

    def __init__(self, file_, format_):
        self._file = file_
        self._format = format_

    def __iter__(self):
        raise NotImplementedError


class Converter(collections.Iterable):
    """
    Responsible for converting records according to format-defined rules, yielding only the specified fields.

    Instances of this type are iterable, returning converted records in file order.
    """
    @classmethod
    def instance(cls, reader, format_, fields=None):
        """
        Return an instance capable of converting records of the specified format.

        :param reader: An iterable file reader.
        :type reader:  Reader
        :param format_: The format definition used to convert the specified file.
        :type format_: bdr.backend.models.Format
        :param fields: A list of file names to include during the conversion.
        :type fields:  list
        :return: A file converter.
        :rtype:  Converter
        """
        return _get_type(format_.module, cls.__name__)(reader, format_, fields)

    def __init__(self, reader, format_, fields=None):
        self._reader = reader
        self._format = format_
        self._fields = fields or []

    def __iter__(self):
        return iter(self._reader)


def _get_type(module_name, class_name):
    module = importlib.import_module(module_name)
    type_object = getattr(module, class_name)
    if not type_object:
        raise ImportError("Appropriate module cannot be found (%s)." % module_name)
    return type_object
